from time import time


class time_meas:

    def __init__( self ):
        self.timeInit = time()
        self.timeSta = 0
        self.timeSto = 0

    def setTimeSta( self ):
        self.timeSta = time()

    def setTimeSto( self ):
        self.timeSto = time()

    def reportTimeRel( self, msg ):  # print relative time to the previous start
        print( "%s : %0.2f s" % ( msg, self.timeSto - self.timeSta ) )

    def reportTimeAbs( self, msg ):
        print( "%s : %0.2f s" % ( msg, self.timeSto - self.timeInit ) )
