void main()
{
    float v = gl_FragCoord.z;
    gl_FragColor = vec4(v, v, v, 1);
}
