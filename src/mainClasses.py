import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# from mainClasses import SoS, ConstituentSystem, Contract
from physicalTwin.lighting.edge.classes import PTLightingEdge
from physicalTwin.fleet.edge.classes import PTFleetEdge
from physicalTwin.bins.edge.classes import PTBinsEdge


class Component:
    def __init__(self,credentials, broker, port):
        self.credentials = credentials
        self.broker=broker
        self.port=port
    def runComponent(self, credentials, broker, port):
        raise NotImplementedError('Subclasses must override the method!')
        
class SoSPTLight(Component):
    def __init__(self,credentials, broker, port, name):
        super().__init__(credentials, broker, port)
        self.name = name
        self.CSs = []  # Aggregation: List of ConstituentSystem instances
        
    def runComponentLighting(self):
        cslight = CSLighting(self.credentials, self.broker, self.port)
        cslight.runPTLighting()
        
        
class SoSPTFleet(Component):
    def __init__(self,credentials, broker, port, name):
        super().__init__(credentials, broker, port)
        self.name = name
        self.CSs = []  # Aggregation: List of ConstituentSystem instances
        

    def runComponentFleet(self):
        csfleet = CSFleet(self.credentials, self.broker, self.port)
        csfleet.runPTFleet()
        
class SoSPTBins(Component):
    def __init__(self,credentials, broker, port, name):
        super().__init__(credentials, broker, port)
        self.name = name
        self.CSs = []  # Aggregation: List of ConstituentSystem instances
        

    def runComponentBins(self):
        csbins = CSBins(self.credentials, self.broker, self.port)
        csbins.runPTBins()
        
class ConstituentSystem:
    """Represents a constituent system in the SoS."""
    def __init__(self, CS_name, credentials, broker, port):
        self.CS_name = CS_name
        self.credentials = credentials
        self.broker=broker
        self.port=port
        self.interdependence = []  # List of other ConstituentSystem instances
        # self.edge = PTEdge()
        
class CSLighting(ConstituentSystem):
    def __init__(self, credentials, broker, port):
        super().__init__("LightingSystem", credentials, broker, port)
        self.edge = PTLightingEdge(credentials, broker, port)
        
    def runPTLighting(self):
        self.edge.startPTedge()  
        
class CSFleet(ConstituentSystem):
    def __init__(self, credentials, broker, port):
        super().__init__("TrucksFleetSystem", credentials, broker, port)
        self.edge = PTFleetEdge(credentials, broker, port)
        
    def runPTFleet(self):
        self.edge.startPTedge()  
        
class CSBins(ConstituentSystem):
    def __init__(self, credentials, broker, port):
        super().__init__("TrashBinsSystem", credentials, broker, port)
        self.edge = PTBinsEdge(credentials, broker, port)
        
    def runPTBins(self):
        self.edge.startPTedge()          
        
# class PTEdge:
#     def __init__(self):
#         self.sensor = PTSensor()
#         self.actuator = PTActuator()
        
    # def startPTedge(self, broker):
    #     self.sensor.startSensor(broker)
    
#     def add_contract(self, contract):
#         """Add a contract to the SoS."""
#         if isinstance(contract, Contract):
#             self.contracts.append(contract)
#         else:
#             raise TypeError("Only Contract instances can be added.")

#     def add_system(self, cs, contract):
#         """
#         Add a constituent system to the SoS if the contract is respected.
#         """
#         if isinstance(cs, ConstituentSystem) and isinstance(contract, Contract):
#             if contract.is_respected(cs):
#                 self.systems.append(cs)
#                 print(f"ConstituentSystem {cs.name} added to SoS under contract: {contract.intent}")
#             else:
#                 print(f"Contract not respected! Cannot add ConstituentSystem {cs.name}.")
#         else:
#             raise TypeError("Invalid types: Expected ConstituentSystem and Contract.")

#     def remove_system(self, cs):
#         """Remove a constituent system from the SoS."""
#         if cs in self.systems:
#             self.systems.remove(cs)
#         else:
#             print(f"ConstituentSystem {cs.name} not found in the SoS.")

#     def evaluate_resilience(self):
#         """Evaluate and return the resilience of the SoS."""
#         resilience = sum(cs.contribute_to_resilience()["resilience_score"] for cs in self.systems)
#         return {"SoS": self.name, "total_resilience_score": resilience}
        

# class ConstituentSystem(SoS):
#     """Represents a constituent system in the SoS."""
#     def __init__(self, credentials, broker, port, name, CS_name):
#         super().__init__(credentials, broker, port, name)
#         self.CS_name = CS_name
#         self.interdependence = []  # List of other ConstituentSystem instances
#         self.edge = PTEdge()
        
#     def runLighting(self):
#         self.edge.startPTedge(self.broker)
        
#     def add_interdependence(self, cs):
#         """Add an interdependent constituent system."""
#         if isinstance(cs, ConstituentSystem):
#             self.interdependence.append(cs)
#         else:
#             raise TypeError("Only ConstituentSystem instances can be added.")

#     # Here
#     def contribute_to_resilience(self):
#         """Calculate and return contribution to resilience."""
#         return {"system": self.name, "resilience_score": "DEFINE A FUNCTION TO DO SO"}  # Example output

#     def emergence_behavior(self):
#         """Return the emergent behavior of the system."""
#         return f"{self.name} exhibits collaborative behavior."

# class Contract:
#     """Represents a contract between an SoS and its constituent systems."""
#     def __init__(self, intent, services, shared_data):
#         self.intent = intent
#         self.services = services
#         self.shared_data = shared_data
#     def is_respected(self, cs):
#         """
#         Validate the contract for the given ConstituentSystem.
#         Replace this logic with actual validation rules.
#         """
        
#         return self.intent in cs.name
        