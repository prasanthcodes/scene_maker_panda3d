#version 330
in vec2 uv;
out vec4 fragColor;
uniform sampler2D p3d_Texture0;
uniform float exposure;
uniform float gamma;
uniform int tonemapping_method;
uniform float param_a;
uniform struct p3d_LightModelParameters {
	vec4 ambient;
} p3d_LightModel;

// tonemapping params
//float param_a = 0.1; // Tone mapping parameter 'a'
float param_Lwhite = 1e3; // White point luminance
float param_hmean = 1.0; // Mean luminance

// Function to compute luminance
float luminance(vec3 rgb) {
    return dot(vec3(0.2126, 0.7152, 0.0722), rgb);
}

void main() {
    // Flip texture horizontally by modifying UV coordinates
    vec2 flippedUV = vec2(1.0 - uv.x, uv.y);
    vec3 color = texture(p3d_Texture0, flippedUV).rgb;
	
	if (tonemapping_method==1){
	// Apply exposure and simple Reinhard tone mapping
	color = color * exposure ;
	color = color / (color + vec3(1.0));
	// Gamma correction
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	} else if (tonemapping_method==2) {
	// extended Reinhard tonemapping
    float Lw = luminance(color);
    float LwAvg = log(param_hmean + 1.0);
    float L = param_a * Lw / LwAvg;
    float Lwhite2 = param_Lwhite * param_Lwhite;
    float Ld = (L * (1.0 + (L / Lwhite2))) / (1.0 + L);
    float Ladj = Ld / Lw;
    // Adjust color and apply gamma correction
    vec3 newXYZ = color * Ladj;
    newXYZ = pow(newXYZ, vec3(0.4545));
    fragColor = vec4(newXYZ, 1.0) * p3d_LightModel.ambient;
	
	}
	
}