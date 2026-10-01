src = open('tools/floating.py').read()
start = src.index('# 2) compenetrazioni')
end = src.index("print('tempo'")
new = open('tools/floating_part2.txt').read()
src = src[:start] + new + src[end:]
src = src.replace("print('contatti', len(E), round(time.time() - t0, 1))", "print('contatti', len(E), round(time.time() - t0, 1), flush=True)")
open('tools/floating.py','w').write(src)
