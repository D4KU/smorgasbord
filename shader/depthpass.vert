uniform mat4 mvp;

in vec3 pos;

void main()
{
    gl_Position = mvp * vec4(pos, 1);
}
