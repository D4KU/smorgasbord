uniform mat4 mvp;

in vec3 pos;

void main()
{
    /* mat4 mvp = proj * view * model; */
    gl_Position = mvp * vec4(pos, 1);
}
