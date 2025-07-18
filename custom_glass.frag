#version 330
uniform sampler2D p3d_Texture0;  // Base color texture
uniform sampler2D p3d_Texture1;  // Metallic-roughness texture
uniform sampler2D p3d_Texture2;  // Normal map
uniform sampler2D p3d_Texture3;  // Transmission texture
uniform samplerCube environmentMap;  // Environment map
uniform float ior;  // Index of refraction
uniform float transmissionFactor;  // Transmission percentage
uniform float envmapIntensity;  // Environment map intensity (new)
in vec3 v_normal;
in vec2 v_texcoord;
in vec3 v_world_position;
out vec4 fragColor;

void main() {
    // Sample glTF textures
    vec4 baseColor = texture(p3d_Texture0, v_texcoord);
    vec2 metallicRoughness = texture(p3d_Texture1, v_texcoord).rg;
    vec3 normal = normalize(texture(p3d_Texture2, v_texcoord).rgb * 2.0 - 1.0);
    float transmission = texture(p3d_Texture3, v_texcoord).r * transmissionFactor;

    // View direction
    vec3 viewDir = normalize(-v_world_position);

    // Fresnel effect
    float fresnel = pow(1.0 - max(dot(normal, -viewDir), 0.0), 5.0);
    fresnel = mix(0.04, 1.0, fresnel);

    // Reflection and pseudo-refraction
    vec3 reflectDir = reflect(viewDir, normal);
    vec3 refractDir = refract(viewDir, normal, 1.0 / ior);
    vec4 reflectionColor = texture(environmentMap, reflectDir)* envmapIntensity;
    vec4 refractionColor = texture(environmentMap, refractDir)* envmapIntensity;

    // Combine
    vec4 glassColor = mix(refractionColor, reflectionColor, fresnel);
    fragColor = mix(baseColor, glassColor, transmission);
    fragColor.a = baseColor.a * transmission;
}