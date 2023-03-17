import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random
from collections import defaultdict

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        modified = {}
        
        # fill assignments dict and keep track of which variables were modified in solve()
        # trailIndex = self.trail.size()
        # print(trailIndex)
        # print(self.trail.trailStack)
        # print(self.trail.getPushCount())

        # selectedVar = self.trail.trailStack[trailIndex-1]
        # selectedVal = selectedVar[0].getValues()[0] 

        # do constraint propogation of neighbor variables within modded constraints (?)
        # making sure to set Modified to False

        moddedConstrs = self.network.getModifiedConstraints()

        for c in moddedConstrs:
            for v in c.vars:
                if v.isAssigned():
                    selectedVar = v
                    selectedVal = v.getAssignment()

                    neighborVars = self.network.getNeighborsOfVariable(selectedVar)
                    for nv in neighborVars:
                        if nv.getDomain().contains(selectedVal) and not nv.isAssigned():
                            self.trail.push(nv)
                            nv.removeValueFromDomain(selectedVal)
                            
                            # if domain becomes 1: trail.push and assign
                            # add to assignments dict
                            if nv.getDomain().size() == 1:
                                nv.assignValue(nv.getValues()[0])
                            modified[nv] = nv.getDomain()
 

        return (modified, self.assignmentsCheck())
        


    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        FC = self.forwardChecking()
        
        norvigDict = {}
        for var in FC[0].keys():
            if var.isAssigned():
                norvigDict[var] = var.getAssignment()
        
        if FC[1] == False:
                return (norvigDict, False)
        
        for constraint in self.network.constraints:
            countDict = defaultdict(int)
            
            for var in constraint.vars:
                for val in var.getDomain().values:
                    countDict[val] += 1
            
            for val in countDict.keys():
                if countDict[val] == 1:
                    for var in constraint.vars:
                        if var.getDomain().contains(val):
                            self.trail.push(var)
                            var.assignValue(val)
                            norvigDict[var] = val

        return (norvigDict, self.assignmentsCheck())

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        
        mV = None
        
        for v in self.network.variables:
            
            if not v.isAssigned():
                
                if mV == None:
                    mV = v
                
                else:
                    if mV.size() >= v.size():
                        mV = v

        return mV

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        mV = None
        mVList = [None]
        for v in self.network.variables:
            
            if not v.isAssigned():
                
                if mV == None:
                    mV = v
                    mVList = [mV]
                else:
                    if mV.size() > v.size():
                        mV = v
                        mVList = [mV]

                    elif mV.size() == v.size():
                        mVNeighbors = self.network.getNeighborsOfVariable(mV)
                        vNeighbors = self.network.getNeighborsOfVariable(v)
                        mVUnassignedNeighbors = 0
                        vUnassignedNeighbors = 0
                        
                        for nv in mVNeighbors:
                            if not nv.isAssigned():
                                mVUnassignedNeighbors+=1
                        
                        for nv in vNeighbors:
                            if not nv.isAssigned():
                                vUnassignedNeighbors+=1

                        if mVUnassignedNeighbors < vUnassignedNeighbors:
                            mV = v
                            mVList = [mV]
                        
                        elif mVUnassignedNeighbors == vUnassignedNeighbors:
                            mVList.append(v)

        return mVList

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        values = v.domain.values
        neighbors = self.network.getNeighborsOfVariable(v)
        
        LCVDict = {}
        for v in values:
            LCVDict[v] = 0
            for n in neighbors:
                if n.getDomain().contains(v):
                    LCVDict[v]+=1
        
        return sorted(LCVDict, key=LCVDict.get)

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )
            # print(self.trail.trailStack)
            # print(self.trail.getPushCount())
            # print("test")

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)


"""
    We thought we had to do Backtracking, whoops
    def _forwardCheck(self, assignments: dict):
        # check completeness, if complete return
        completeAssignment = False
        
        if(completeAssignment):
            isComplete = True 
            for var in assignments:
                if(var.isAssigned()):

        if(False):
            return (assignments, True)

        # else
        var = self.selectNextVariable(self)
        for val in self.getNextValues(var):
            # assign value?
            isConsistent = self.assignmentsCheck()
            if(isConsistent):
                #
                if ():
                    # assign variable officially
                    # eliminate value from neighbors
                    return self._forwardCheck(assignments)
            
            else:
                
                return
        
        return (assignments, False)
"""
