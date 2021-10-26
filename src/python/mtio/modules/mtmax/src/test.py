class Number:
    def __init__( self, value=0 ):
        self.value = value

print( hash((1, 2, 3)) == hash((1, 2, 3)) )
print( hash((Number(1), Number(2), Number(3))) == hash((Number(1), Number(2), Number(3))) )