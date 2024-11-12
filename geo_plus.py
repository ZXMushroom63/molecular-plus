import bpy
import bmesh

def add_geometry_nodes_modifier(obj, frame_frequency):
    mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
    tree = bpy.data.node_groups.new(name="ParticleDataTransfer", type='GeometryNodeTree')
    mod.node_group = tree
    nodes = tree.nodes
    links = tree.links
    interface = tree.interface

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)
        
    interface.new_socket(
        name='Geometry',
        in_out='INPUT',
        socket_type='NodeSocketGeometry'
    )
    interface.new_socket(
        name='Geometry',
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Add nodes
    frame_frequency_node = nodes.new(type='FunctionNodeInputInt')
    frame_frequency_node.integer = frame_frequency
    frame_frequency_node.name = "Frame Frequency"

    scene_time_node = nodes.new(type='GeometryNodeInputSceneTime')
    divide_node = nodes.new(type='ShaderNodeMath')
    divide_node.operation = 'DIVIDE'
    ceil_node = nodes.new(type='ShaderNodeMath')
    ceil_node.operation = 'CEIL'
    multiply_node = nodes.new(type='ShaderNodeMath')
    multiply_node.operation = 'MULTIPLY'
    truncate_node = nodes.new(type='FunctionNodeFloatToInt')
    value_to_string_node = nodes.new(type='FunctionNodeValueToString')
    value_to_string_node.inputs['Decimals'].default_value = 0
    value_to_string_node.name = "Frame Suffix"
    string_constant_node = nodes.new(type='FunctionNodeInputString')
    string_constant_node.string = "velocity"
    string_constant_node_mt = nodes.new(type='FunctionNodeInputString')
    string_constant_node_mt.string = "meta"
    join_strings_node = nodes.new(type='GeometryNodeStringJoin')
    join_strings_node.inputs['Delimiter'].default_value = "_"
    join_strings_node_mt = nodes.new(type='GeometryNodeStringJoin')
    join_strings_node_mt.inputs['Delimiter'].default_value = "_"
    named_attribute_node = nodes.new(type='GeometryNodeInputNamedAttribute')
    named_attribute_node.data_type = 'FLOAT_VECTOR'
    named_attribute_node_mt = nodes.new(type='GeometryNodeInputNamedAttribute')
    named_attribute_node_mt.data_type = 'FLOAT_VECTOR'
    store_named_attribute_node = nodes.new(type='GeometryNodeStoreNamedAttribute')
    store_named_attribute_node.data_type = 'FLOAT_VECTOR'
    store_named_attribute_node.inputs['Name'].default_value = "velocity"
    store_named_attribute_node_mt = nodes.new(type='GeometryNodeStoreNamedAttribute')
    store_named_attribute_node_mt.data_type = 'FLOAT_VECTOR'
    store_named_attribute_node_mt.inputs['Name'].default_value = "meta"
    group_input = nodes.new(type='NodeGroupInput')
    group_output = nodes.new(type='NodeGroupOutput')

    # Create links
    links.new(scene_time_node.outputs['Frame'], divide_node.inputs[0])
    links.new(frame_frequency_node.outputs[0], divide_node.inputs[1])
    links.new(divide_node.outputs['Value'], ceil_node.inputs[0])
    links.new(ceil_node.outputs['Value'], multiply_node.inputs[0])
    links.new(frame_frequency_node.outputs[0], multiply_node.inputs[1])
    links.new(multiply_node.outputs['Value'], truncate_node.inputs[0])
    links.new(truncate_node.outputs['Integer'], value_to_string_node.inputs['Value'])
    
    links.new(value_to_string_node.outputs['String'], join_strings_node.inputs[1])
    links.new(string_constant_node.outputs['String'], join_strings_node.inputs[1])
    
    links.new(value_to_string_node.outputs['String'], join_strings_node_mt.inputs[1])
    links.new(string_constant_node_mt.outputs['String'], join_strings_node_mt.inputs[1])
    
    links.new(join_strings_node.outputs['String'], named_attribute_node.inputs['Name'])
    links.new(named_attribute_node.outputs['Attribute'], store_named_attribute_node.inputs['Value'])
    links.new(group_input.outputs[0], store_named_attribute_node.inputs['Geometry'])
    links.new(store_named_attribute_node.outputs['Geometry'], store_named_attribute_node_mt.inputs['Geometry'])
    
    links.new(join_strings_node_mt.outputs['String'], named_attribute_node_mt.inputs['Name'])
    links.new(named_attribute_node_mt.outputs['Attribute'], store_named_attribute_node_mt.inputs['Value'])
    links.new(store_named_attribute_node_mt.outputs['Geometry'], group_output.inputs[0])




n = 1  # change this value to skip every n frames

def create_velocity_layer(mesh, frame):
    layer_name = f"velocity_{frame}"
    if layer_name not in mesh.attributes:
        mesh.attributes.new(name=layer_name, type='FLOAT_VECTOR', domain='POINT')
    return mesh.attributes[layer_name]

def create_meta_layer(mesh, frame):
    layer_name = f"meta_{frame}"
    if layer_name not in mesh.attributes:
        mesh.attributes.new(name=layer_name, type='FLOAT_VECTOR', domain='POINT')
    return mesh.attributes[layer_name]

def to_geo_plus(obj):
    # Ensure the object has a particle system
    if obj.particle_systems:
        # Dependency graph
        degp = bpy.context.evaluated_depsgraph_get()

        # Evaluate the depsgraph (Important step)
        evaluated_obj = obj.evaluated_get(degp)
        particle_system = evaluated_obj.particle_systems[0]

        # Create a new mesh to store the particle positions
        mesh = bpy.data.meshes.new("ParticleMesh")
        particle_obj = bpy.data.objects.new("ParticleObject", mesh)
        bpy.context.collection.objects.link(particle_obj)

        # Initialize the mesh with vertices from the first frame
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)
        bm = bmesh.new()
        for particle in particle_system.particles:
            bm.verts.new(particle.location)
        bm.to_mesh(mesh)
        bm.free()
        particle_obj.data.update()

        # Add a Basis Shape Key
        particle_obj.shape_key_add(name="Basis")

        # Set up animation
        frame_start = particle_system.point_cache.frame_start
        frame_end = particle_system.point_cache.frame_end

        # Ensure velocity layer for frame 0 is created
        bpy.context.scene.frame_set(frame_start)
        particles = particle_system.particles
        total_particles = len(particles)
        locations = [0] * (3 * total_particles)
        velocities = [0] * (3 * total_particles)
        particle_meta = [0] * (3 * total_particles)
        particles.foreach_get("location", locations)
        particles.foreach_get("velocity", velocities)
        particles.foreach_get("angular_velocity", particle_meta)

        velocity_layer_0 = create_velocity_layer(mesh, frame_start)
        meta_layer_0 = create_meta_layer(mesh, frame_start)
        
        for i in range(total_particles):
            vx, vy, vz = velocities[i*3], velocities[i*3 + 1], velocities[i*3 + 2]
            velocity_layer_0.data[i].vector = (vx, vy, vz)
            
            ax, ay, az = particle_meta[i*3], particle_meta[i*3 +1], particle_meta[i*3 + 2]
            meta_layer_0.data[i].vector = (ax, ay, az)
        
        for frame in range(frame_start, frame_end + 1):
            if frame % n != 0:  # Skip keyframing every n frames
                continue

            bpy.context.scene.frame_set(frame)

            particles = particle_system.particles
            total_particles = len(particles)
            locations = [0] * (3 * total_particles)
            velocities = [0] * (3 * total_particles)
            particle_meta = [0] * (3 * total_particles)

            particles.foreach_get("location", locations)
            particles.foreach_get("velocity", velocities)
            particles.foreach_get("angular_velocity", particle_meta)

            shape_key = particle_obj.shape_key_add(name=f"Frame_{frame}")
            velocity_layer = create_velocity_layer(mesh, frame)

            for i in range(total_particles):
                x, y, z = locations[i*3], locations[i*3 + 1], locations[i*3 + 2]
                vx, vy, vz = velocities[i*3], velocities[i*3 + 1], velocities[i*3 + 2]

                shape_key.data[i].co = (x, y, z)
                
                velocity_layer.data[i].vector = (vx, vy, vz)
            
            meta_layer = create_meta_layer(mesh, frame)
            for i in range(total_particles):
                ax, ay, az = particle_meta[i*3], particle_meta[i*3 + 1], particle_meta[i*3 + 2]
                meta_layer.data[i].vector = (ax, ay, az)
                
            shape_key.value = 1.0
            shape_key.keyframe_insert(data_path="value", frame=frame)
            shape_key.value = 0.0
            shape_key.keyframe_insert(data_path="value", frame=frame - n)
            shape_key.keyframe_insert(data_path="value", frame=frame + n)

            for fcurve in particle_obj.data.shape_keys.animation_data.action.fcurves:
                for keyframe_point in fcurve.keyframe_points:
                    keyframe_point.interpolation = 'LINEAR'
        add_geometry_nodes_modifier(particle_obj, n)
        return particle_obj
    else:
        return None