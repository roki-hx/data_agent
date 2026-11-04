import dataclasses
from pathlib import Path

import omegaconf
import yaml
from attr import dataclass
from omegaconf import OmegaConf


def lad_by_yaml():
#定义文件路径对象
    yaml_path = Path(__file__).parents[2] / "conf" / "config.yaml"
    with open(yaml_path , mode="r" ,encoding="utf-8") as file:
        yaml_data = yaml.safe_load(file)
        print(yaml_data)
        print(type(yaml_data))

@dataclass
class persoon:
    name : str
    age : int
    height : float


def lad_by_omega():
    #定义文件路径对象
    yaml_path = Path(__file__).parents[2] / "conf" / "config.yaml"
    data = OmegaConf.load(yaml_path)
    print(data)
    print(type(data))

    person_config : persoon = OmegaConf.to_object(OmegaConf.merge(persoon,data))
    print(person_config,type(person_config))
    print(person_config.name)

if __name__ == '__main__':
    lad_by_omega()