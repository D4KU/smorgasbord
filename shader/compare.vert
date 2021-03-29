const float bias = 0.01f;

uniform mat4 mvp;
uniform sampler2D depthtex;

in vec3 pos;
out vec4 col;

void main()
{
    gl_Position = mvp * vec4(pos, 1);
    vec2 uv = (gl_Position.xy / gl_Position.w) * 0.5f + 0.5f;
    vec4 depth = texture(depthtex, uv);

    /* bool visible = (gl_Position.z + bias) < depth.r; */
    /* col = vec4(visible, visible, visible, 1.f); */
    /* col = vec4(uv.x, uv.y, 0.f, 1.f); */
    col = depth;
}
