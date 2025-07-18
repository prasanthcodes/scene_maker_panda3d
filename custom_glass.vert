#version 330
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
out vec3 v_normal;
out vec2 v_texcoord;
out vec3 v_world_position;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = normalize(mat3(p3d_ModelViewMatrix) * p3d_Normal);
    v_texcoord = p3d_MultiTexCoord0;
    v_world_position = (p3d_ModelViewMatrix * p3d_Vertex).xyz;
}