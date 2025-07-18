#version 330
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
out vec3 v_normal;
out vec4 v_position;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = normalize(p3d_Normal);
    v_position = p3d_Vertex;
}