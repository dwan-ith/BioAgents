import hyperon as hn

space = hn.Space()

def init_metta():
    global space
    with open('molecules.metta', 'r') as f:
        code = f.read()
    runner = hn.Runner(space)
    runner.run(code)
    print("MeTTa initialized")

def query(query_str):
    runner = hn.Runner(space)
    result = runner.run(query_str)
    print(f"Query result: {result}")
    return result

if __name__ == "__main__":
    init_metta()
    test_query = "(find ?compound (molecule ?compound))"
    query(test_query)