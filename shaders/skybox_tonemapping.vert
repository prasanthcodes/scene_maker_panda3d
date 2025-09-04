#version 330
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 uv;
uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
	gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
	uv = p3d_MultiTexCoord0;
}