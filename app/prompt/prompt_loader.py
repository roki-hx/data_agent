from pathlib import Path


#读取提示词文件
def load_prompt(name: str):
    path = Path(__file__).parents[2] / "prompts" / f"{name}.prompt"
    return path.read_text(encoding="utf-8")

if __name__ == '__main__':
    print(load_prompt("plan_sql"))