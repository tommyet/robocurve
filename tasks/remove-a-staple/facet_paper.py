"""Finite rigid-facet paper candidate with native passive bending hinges.

Adapted from this repository's unpick-a-seam/facet_cloth.py. The paper candidate
uses physical100µm facets, paper flexural rigidity and finite native break force.
Only a coupon diagnostic is currently available, not a validated task.

This is an approximately inextensible paper model, not surface FEM. Each
triangle is a free thin convex prism in the earlier candidate; the box
candidate uses an analytic100µm rectangular prism and avoids convex cooking. Shared edges have ordinary revolute
joints and finite bending springs; no body is attached to the world. Adjacent
material facets share collision exclusions, while all steel-staple contacts remain
enabled. Native deflection/contact evidence is required before using it.
"""
from collections import defaultdict
from dataclasses import dataclass
import math
import numpy as np



@dataclass(frozen=True)
class ShellMaterial:
    thickness_m: float=.0001
    density_kg_m3: float=800.
    bend_modulus_pa: float=2e9
    poissons_ratio: float=.3
    damping_ratio: float=.15
    friction: float=.35
    # Weak-direction copy-paper tensile index19.31kNm/kg ×78.7gsm ≈1520N/m.
    # This is an engineering envelope, not calibrated puncture fracture.
    tensile_strength_per_width_n_m: float=1500.

    @property
    def rigidity_nm(self):
        return self.bend_modulus_pa*self.thickness_m**3/(12*(1-self.poissons_ratio**2))


def coupon_mesh():
    """24×20mm paper coupon with two true0.8×0.6mm punctures."""
    from generate_meshes import make
    return make((.024,.020),((-.0064,0.),(.0064,0.)),(.0006,.0008),spacing=.004,profile='clearance-candidate')


def rectangular_panel_mesh(size,centres,hole_size,spacing=.012):
    """Rectangular analytic panels with exact outer edges and open punctures.

    Paired inspection triangles form each native panel. Feature-aligned grid
    lines are kept exact; a coarse line within0.3mm of one is omitted to avoid
    an accidental sliver unrelated to the paper geometry.
    """
    from paper import PaperMesh
    holes=[[c[0]-hole_size[0]/2,c[0]+hole_size[0]/2,
            c[1]-hole_size[1]/2,c[1]+hole_size[1]/2] for c in centres]
    axes=[]
    for axis,extent in enumerate(size):
        features=[-extent/2,extent/2]
        for centre in centres:
            for sign in (-1,1):
                features.extend(centre[axis]+sign*(hole_size[axis]/2+d)
                                for d in (0.,.0016,.004))
        features=np.unique(np.round([x for x in features if -extent/2<=x<=extent/2],10))
        regular=np.linspace(-extent/2,extent/2,int(np.ceil(extent/spacing))+1)
        axes.append(np.sort(np.r_[features,[x for x in regular if np.min(np.abs(features-x))>=.0003]]))
    return _rectangular_mesh(*axes,holes)


def _rectangular_mesh(xs,ys,holes):
    from paper import PaperMesh
    points=[];faces=[];lookup={}
    def vertex(i,j):
        if (i,j) not in lookup:
            lookup[i,j]=len(points);points.append((xs[i],ys[j],0.))
        return lookup[i,j]
    for j in range(len(ys)-1):
        for i in range(len(xs)-1):
            x,y=(xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2
            if any(x0<x<x1 and y0<y<y1 for x0,x1,y0,y1 in holes):continue
            a,b,c,d=vertex(i,j),vertex(i+1,j),vertex(i+1,j+1),vertex(i,j+1)
            faces.extend(((a,b,c),(a,c,d)))
    mesh=PaperMesh(np.asarray(points),np.asarray(faces,int),holes);mesh.audit();return mesh


def box_coupon_mesh():
    """Same coupon dimensions/holes, partitioned into rectangular panels."""
    xs=np.array((-.012,-.010,-.008,-.0067,-.0061,-.004,-.002,0.,.002,.004,.0061,.0067,.008,.010,.012))
    ys=np.array((-.010,-.008,-.006,-.004,-.002,-.0004,.0004,.002,.004,.006,.008,.010))
    holes=[[-.0067,-.0061,-.0004,.0004],[.0061,.0067,-.0004,.0004]]
    return _rectangular_mesh(xs,ys,holes)


def box_task_mesh(index):
    """Full210×148mm sheet candidate, matching the established task layout."""
    from full_scene import SHEET_CENTRES,STAPLE_XY
    cx,cy=SHEET_CENTRES[index]
    centres=[(STAPLE_XY[0]-cx,STAPLE_XY[1]+side*.0064-cy) for side in (-1,1)]
    return rectangular_panel_mesh((.21,.148),centres,(.0008,.0006))


def rotation_quaternion(matrix):
    from scipy.spatial.transform import Rotation
    return Rotation.from_matrix(matrix).as_quat()


def mechanics(mesh,material=ShellMaterial(),primitive_boxes=False):
    vertex_ids=mesh.faces
    if primitive_boxes:
        if len(mesh.faces)%2:raise ValueError('Box panels require paired rectangular triangles')
        ids=[]
        for first,second in zip(mesh.faces[::2],mesh.faces[1::2]):
            if first[0]!=second[0] or first[2]!=second[1]:
                raise ValueError('Triangle pair does not describe one rectangle')
            ids.append((first[0],first[1],first[2],second[2]))
        vertex_ids=np.asarray(ids,int)
    points=mesh.rest[vertex_ids];centres=points.mean(1)
    cross=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0])
    areas=np.linalg.norm(cross,axis=1)/2;normals=cross/(2*areas[:,None])
    if primitive_boxes:
        edge1,edge2=points[:,1]-points[:,0],points[:,3]-points[:,0]
        if not (np.allclose(points[:,2],points[:,0]+edge1+edge2,atol=1e-12) and
                np.allclose(np.sum(edge1*edge2,axis=1),0.,atol=1e-14)):
            raise ValueError('Native box panels must be rectangles')
        areas*=2
    masses=areas*material.thickness_m*material.density_kg_m3
    edges=defaultdict(list);vertices=defaultdict(list)
    for face,ids in enumerate(vertex_ids):
        for vertex in ids:vertices[int(vertex)].append(face)
        for a,b in zip(ids,np.roll(ids,-1)):edges[tuple(sorted((int(a),int(b))))].append(face)
    neighbours=[set() for _ in points]
    for touching in vertices.values():
        for face in touching:neighbours[face].update(set(touching)-{face})
    hinges=[]
    for edge,owners in sorted(edges.items()):
        if len(owners)!=2:continue
        i,j=owners;a,b=mesh.rest[list(edge)];direction=b-a;length=np.linalg.norm(direction)
        axis=direction/length;normal=normals[i];frame=np.column_stack((axis,np.cross(normal,axis),normal))
        anchor=(a+b)/2
        width=sum(np.linalg.norm(np.cross(centres[k]-anchor,axis)) for k in owners)
        stiffness=material.rigidity_nm*length/width
        inertia=[]
        for k in owners:
            rel=points[k]-anchor;perpendicular=rel-(rel@axis)[:,None]*axis
            if primitive_boxes:
                offset=centres[k]-anchor;offset-=np.dot(offset,axis)*axis
                around_centre=perpendicular-offset
                inertia.append(masses[k]*(np.dot(offset,offset)+np.sum(around_centre**2)/12+
                                          material.thickness_m**2/12))
            else:
                inertia.append(masses[k]*((np.sum(perpendicular**2)+np.sum(perpendicular.sum(0)**2))/12
                                          +material.thickness_m**2/12))
        effective=inertia[0]*inertia[1]/sum(inertia)
        damping=2*material.damping_ratio*math.sqrt(stiffness*effective)
        hinges.append(dict(edge=edge,faces=owners,anchor=anchor,frame=frame,
                           stiffness_nm_rad=stiffness,damping_nms_rad=damping,
                           break_force_n=material.tensile_strength_per_width_n_m*length))
    endpoint_pairs=[]
    for hinge in hinges:
        i,j=hinge['faces']
        for vertex in hinge['edge']:
            endpoint_pairs.append((i,int(np.flatnonzero(vertex_ids[i]==vertex)[0]),
                                   j,int(np.flatnonzero(vertex_ids[j]==vertex)[0])))
    return dict(points=points,centres=centres,normals=normals,masses=masses,
                neighbours=neighbours,hinges=hinges,
                endpoint_pairs=np.asarray(endpoint_pairs,int).reshape(-1,4),
                vertex_ids=vertex_ids,primitive_boxes=primitive_boxes)


def author_shell(stage,path,mesh,material=ShellMaterial(),color=(.94,.94,.91),*,primitive_boxes=False,velocity_iterations=4,position_iterations=128):
    """Author only before simulation. All shell facet bodies remain dynamic."""
    from pxr import Gf,Sdf,UsdGeom,UsdPhysics,PhysxSchema,UsdShade,Vt
    if velocity_iterations not in (1,4,32):raise ValueError('Unsupported diagnostic velocity iterations')
    if position_iterations not in (32,64,128):raise ValueError('Unsupported diagnostic position iterations')
    model=mechanics(mesh,material,primitive_boxes);bodies=[];joints=[]
    mat=UsdShade.Material.Define(stage,path+'/Material')
    pm=UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
    pm.CreateStaticFrictionAttr(material.friction);pm.CreateDynamicFrictionAttr(material.friction)
    pm.CreateRestitutionAttr(0.)
    prism_faces=((0,2,1),(3,4,5),(0,1,4),(0,4,3),(1,2,5),(1,5,4),(2,0,3),(2,3,5))
    for i,(points,centre,normal,mass) in enumerate(zip(model['points'],model['centres'],model['normals'],model['masses'])):
        root=UsdGeom.Xform.Define(stage,f'{path}/facet_{i:03d}')
        root.AddTranslateOp().Set(Gf.Vec3d(*centre));prim=root.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim);UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(float(mass))
        rb=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        rb.CreateSolverPositionIterationCountAttr(position_iterations);rb.CreateSolverVelocityIterationCountAttr(velocity_iterations)
        rb.CreateMaxDepenetrationVelocityAttr(.05)
        rb.CreateEnableCCDAttr(True);rb.CreateSleepThresholdAttr(0.)
        rb.CreateLinearDampingAttr(0.);rb.CreateAngularDampingAttr(0.)
        local=points-centre
        if primitive_boxes:
            shape=UsdGeom.Cube.Define(stage,str(root.GetPath())+'/Shape')
            shape.CreateSizeAttr(1.)
            x,y=points[1]-points[0],points[3]-points[0]
            width,height=np.linalg.norm(x),np.linalg.norm(y)
            q=rotation_quaternion(np.column_stack((x/width,y/height,normal)))
            shape.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(float(q[3]),Gf.Vec3d(*q[:3])))
            shape.AddScaleOp().Set(Gf.Vec3d(width,height,material.thickness_m))
        else:
            shape=UsdGeom.Mesh.Define(stage,str(root.GetPath())+'/Shape')
            vertices=np.vstack((local-normal*material.thickness_m/2,local+normal*material.thickness_m/2))
            shape.CreatePointsAttr(Vt.Vec3fArray(vertices.tolist()))
            shape.CreateFaceVertexCountsAttr([3]*len(prism_faces));shape.CreateFaceVertexIndicesAttr(np.ravel(prism_faces).tolist())
            shape.CreateSubdivisionSchemeAttr('none');shape.CreateDoubleSidedAttr(True)
        shape.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
        if not primitive_boxes:
            UsdPhysics.MeshCollisionAPI.Apply(shape.GetPrim()).CreateApproximationAttr('convexHull')
            hull=PhysxSchema.PhysxConvexHullCollisionAPI.Apply(shape.GetPrim())
            hull.CreateMinThicknessAttr(float(material.thickness_m/4))
        cp=PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim())
        cp.CreateContactOffsetAttr(.000002);cp.CreateRestOffsetAttr(0.)
        UsdShade.MaterialBindingAPI.Apply(shape.GetPrim()).Bind(mat,UsdShade.Tokens.weakerThanDescendants,'physics')
        UsdPhysics.FilteredPairsAPI.Apply(prim).CreateFilteredPairsRel().SetTargets(
            [Sdf.Path(f'{path}/facet_{j:03d}') for j in sorted(model['neighbours'][i])])
        bodies.append(str(root.GetPath()))
    for k,hinge in enumerate(model['hinges']):
        i,j=hinge['faces'];joint=UsdPhysics.RevoluteJoint.Define(stage,f'{path}/hinge_{k:03d}')
        joint.CreateBody0Rel().SetTargets([Sdf.Path(bodies[i])]);joint.CreateBody1Rel().SetTargets([Sdf.Path(bodies[j])])
        q=rotation_quaternion(hinge['frame']);rotation=Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3]))
        joint.CreateLocalPos0Attr(Gf.Vec3f(*(hinge['anchor']-model['centres'][i])))
        joint.CreateLocalPos1Attr(Gf.Vec3f(*(hinge['anchor']-model['centres'][j])))
        joint.CreateLocalRot0Attr(rotation);joint.CreateLocalRot1Attr(rotation)
        joint.CreateAxisAttr('X');joint.CreateCollisionEnabledAttr(False)
        joint.CreateBreakForceAttr(float(hinge['break_force_n']))
        drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'angular');drive.CreateTypeAttr('force')
        drive.CreateTargetPositionAttr(0.);drive.CreateTargetVelocityAttr(0.)
        drive.CreateStiffnessAttr(float(hinge['stiffness_nm_rad']*math.pi/180))
        drive.CreateDampingAttr(float(hinge['damping_nms_rad']*math.pi/180))
        drive.CreateMaxForceAttr(float(2*math.pi*hinge['stiffness_nm_rad']))
        joints.append(str(joint.GetPath()))
    return dict(bodies=bodies,joints=joints,mesh=mesh,model=model,material=material)


def measured_surface(shell,poses):
    """Reconstruct mean shared vertices and measure actual joint consistency.

    Averaging never excuses gaps: maximum endpoint disagreement is separately
    reported and must remain below the explicit25µm numerical envelope.
    """
    from scipy.spatial.transform import Rotation
    poses=np.asarray(poses,float);mesh=shell['mesh'];model=shell['model']
    ids=model['vertex_ids']
    if poses.shape!=(len(ids),7) or not np.isfinite(poses).all():raise ValueError('Invalid facet poses')
    rotations=Rotation.from_quat(poses[:,3:]).as_matrix()
    world=np.einsum('fij,fvj->fvi',rotations,model['points']-model['centres'][:,None])+poses[:,:3,None].transpose(0,2,1)
    summed=np.zeros_like(mesh.rest);count=np.zeros(len(mesh.rest),int)
    np.add.at(summed,ids.ravel(),world.reshape(-1,3));np.add.at(count,ids.ravel(),1)
    points=summed/count[:,None]
    disagreement=np.linalg.norm(world-points[ids],axis=-1)
    pairs=model['endpoint_pairs']
    delta=world[pairs[:,0],pairs[:,1]]-world[pairs[:,2],pairs[:,3]]
    magnitudes=np.linalg.norm(delta,axis=1);worst=int(np.argmax(magnitudes))
    gap=float(magnitudes[worst])
    result=dict(maximum_hinge_endpoint_gap_m=gap,
                maximum_vertex_average_error_m=float(disagreement.max()),valid=gap<=.000025)
    if gap>.0000125:
        pair=pairs[worst]
        result['worst_endpoint']=dict(panel_indices=[int(pair[0]),int(pair[2])],
            positions_m=[world[pair[0],pair[1]].tolist(),world[pair[2],pair[3]].tolist()],
            difference_m=delta[worst].tolist())
    return points,result


def cooked_hull_geometry(shell,stage):
    """Request native collision hulls; no geometry or pose writes.

    Use the stage-aware PhysX110 API demonstrated by ConvexMeshDataDemo. Failure
    must be reported rather than substituting authored mesh dimensions.
    """
    from omni.physx import get_physx_cooking_interface
    from omni.physx.bindings._physx import PhysxCollisionRepresentationResult
    from pxr import UsdUtils,PhysicsSchemaTools
    cooking=get_physx_cooking_interface();rows=[]
    stage_id=UsdUtils.StageCache.Get().GetId(stage).ToLongInt()
    for i,body in enumerate(shell['bodies']):
        path=body+'/Shape';received=[]
        def on_result(result,convexes):received.append((result,convexes))
        cooking.request_convex_collision_representation(stage_id=stage_id,
            collision_prim_id=PhysicsSchemaTools.sdfPathToInt(path),
            run_asynchronously=False,on_result=on_result)
        if len(received)!=1 or received[0][0]!=PhysxCollisionRepresentationResult.RESULT_VALID:
            raise RuntimeError(f'Native collision representation unavailable for {path}: {received}')
        convexes=received[0][1]
        if len(convexes)!=1:raise RuntimeError(f'Expected one cooked hull for {path}, found {len(convexes)}')
        vertices=np.asarray([[v.x,v.y,v.z] for v in convexes[0].vertices],float)
        if vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<4:
            raise RuntimeError(f'Invalid cooked vertices for {path}')
        normal=shell['model']['normals'][i]
        rows.append(dict(body=i,vertices=len(vertices),
                         thickness_m=float(np.ptp(vertices@normal)),
                         axis_extents_m=np.ptp(vertices,axis=0).tolist()))
    return dict(source='native PhysX collision-representation vertices',facets=rows,
                minimum_thickness_m=min(row['thickness_m'] for row in rows),
                maximum_thickness_m=max(row['thickness_m'] for row in rows))
