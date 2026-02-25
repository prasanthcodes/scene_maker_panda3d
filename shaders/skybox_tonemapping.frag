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
float Lwhite = 50.0;

// Function to compute luminance
float luminance(vec3 rgb) {
	// Compute luminance (using BT.709 weights for modern displays; alternatives: 0.299,0.587,0.114)
    return dot(vec3(0.2126, 0.7152, 0.0722), rgb);
}

vec3 reinhardPhotographic(vec3 color, float white) {
    float L = luminance(color);
    float Ld = (L * (1.0 + (L / (white * white)))) / (1.0 + L);
    return color * (Ld / L);
}

const mat3 aces_input_matrix = mat3(
    0.59719, 0.07600, 0.02840,
    0.35458, 0.90834, 0.13383,
    0.04823, 0.01566, 0.83777
);

const mat3 aces_output_matrix = mat3(
     1.60475, -0.10208, -0.00327,
    -0.53108,  1.10813, -0.07276,
    -0.07367, -0.00605,  1.07602
);

vec3 rtt_and_odt_fit(vec3 v)
{
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return a / b;
}

vec3 aces_fitted(vec3 v)
{
    v = aces_input_matrix * v;
    v = rtt_and_odt_fit(v);
    return aces_output_matrix * v;
}


vec3 PBRNeutralToneMapping( vec3 color ) {
  const float startCompression = 0.8 - 0.04;
  const float desaturation = 0.15;

  float x = min(color.r, min(color.g, color.b));
  float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
  color -= offset;

  float peak = max(color.r, max(color.g, color.b));
  if (peak < startCompression) return color;

  const float d = 1. - startCompression;
  float newPeak = 1. - d * d / (peak + d - startCompression);
  color *= newPeak / peak;

  float g = 1. - 1. / (desaturation * (peak - newPeak) + 1.);
  return mix(color, newPeak * vec3(1, 1, 1), g);
}


void main() {
    // Flip texture horizontally by modifying UV coordinates
    vec2 flippedUV = vec2(1.0 - uv.x, uv.y);
    vec3 color = texture(p3d_Texture0, flippedUV).rgb;
	
	if (tonemapping_method==1){
	// Apply exposure and Linear clamp/saturate
	color = color * exposure;
	color = clamp(color, 0.0, 1.0);
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	} else if (tonemapping_method==2){
	// Apply exposure and simple Reinhard tone mapping
	color = color * exposure;
	color = color / (color + vec3(1.0));
	// Gamma correction
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	} else if (tonemapping_method==3) {
	// reinhardPhotographic from https://viewer.openhdr.org
	color = color * exposure;
	color = reinhardPhotographic(color, Lwhite);
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	} else if (tonemapping_method==4) {
	// ACES tonemapping from https://viewer.openhdr.org
	color = color * exposure;
	color = aces_fitted(color);
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	} else if (tonemapping_method==5) {
	// pbrNeutral tonemapping from https://github.com/KhronosGroup/ToneMapping/blob/main/PBR_Neutral/pbrNeutral.glsl
	color = color * exposure;
	color = PBRNeutralToneMapping(color);
	color = pow(color, vec3(1.0/gamma));
	fragColor = vec4(color, 1.0) * p3d_LightModel.ambient;
	
	}
	
	
}

