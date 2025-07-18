#version 330
uniform float ior;  // Index of refraction (e.g., 1.5 for glass)
uniform samplerCube environmentMap;  // Environment map for reflections
in vec3 v_normal;
in vec4 v_position;
out vec4 fragColor;

void main() {
    vec3 normal = normalize(v_normal);
    vec3 viewDir = normalize(-v_position.xyz);
    // Simplified refraction calculation
    vec3 refractDir = refract(viewDir, normal, 1.0 / ior);
    vec4 reflectionColor = texture(environmentMap, reflect(viewDir, normal));
    vec4 refractionColor = texture(environmentMap, refractDir);
    // Blend reflection and refraction (adjust weights as needed)
    fragColor = mix(reflectionColor, refractionColor, 0.5);
    fragColor.a = 0.5;  // Adjust transparency for glass
}