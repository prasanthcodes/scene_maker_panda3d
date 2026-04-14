#version 330

// Inputs from Panda3D
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

// The magic uniform: this holds your scale, offset, and rotation
uniform mat3 p3d_TextureMatrix0; 
uniform mat4 p3d_ModelViewProjectionMatrix;

out vec2 uv;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;
}