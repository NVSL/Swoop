import argparse
import Swoop.Swoop as swp
import BECPModule

parser = argparse.ArgumentParser(description='Basic EAGLE code processor. Runs text in EAGLE "Code" layer.')
 
parser.add_argument("-s", metavar="sch", type=str, help="The EAGLE schematic to process")

args = parser.parse_args()

file_name = args.s

print ("Running EAGLE code processor")

sch = swp.EagleFile.from_file(file_name)
        
main = BECPModule(sch)
main.process()
main.save("test.processes.sch")
