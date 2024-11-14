#inbounds,0,0,0,1,1,1:settemp,-1000
#TO
#[ - program
#   [ - line
#       [0,0,0,0,1,1,1], - instruction
#       [1,-1000]  - instruction
#   ]   
#]

opcodes = {
    "inbounds": 0,
    "settemp": 1,
    "addtemp": 2
}
def to_ast(script: str):
    output = []
    instructions = script.split("\n")
    for instruction in instructions:
        lineout = []
        components = instruction.split(":")
        for component in components:
            segments = component.split(",")
            lineout.append([opcodes[segments[0]], *map(lambda x: float(x), segments[1:])])
        output.append(lineout)
        
    return output