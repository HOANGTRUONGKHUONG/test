
def parseRule(path,id):
    string = ["SecRule","id:"]
    dataNotCmt,lineNumber,rules=[],[],[]
    with open(path, "r") as file:
        data=file.readlines()
    for i in range(len(data)):
        if data[i][0]!="#":
            dataNotCmt.append(data[i])
    for num in range(len(dataNotCmt)):
        line=dataNotCmt[num].split(" ")
        if line[0]==string[0]:
            lineNumber.append(num)
    for i in range(len(lineNumber)-1):
        rules.append(" ".join(dataNotCmt[lineNumber[i]:lineNumber[i+1]]))
    lastRule=""
    for i in dataNotCmt[lineNumber[-1]:len(dataNotCmt)]:
        lastRule = lastRule + i
        if i=="\n":
            rules.append(lastRule)
            break 
        else:
            rules.append(lastRule)
    for rule in rules:
        if id in rule:
            return rule 
