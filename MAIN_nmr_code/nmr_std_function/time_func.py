from time import time


class time_meas:

    def __init__( self , en ):
        # set en to True if time measurement is necessary, set en to False in order to bypass time measurement and speed up the loop
        self.en = en
        if ( self.en ):
            self.timeInit = time()
            self.timeSta = 0
            self.timeSto = 0

    def setTimeSta( self ):
        if ( self.en ):
            self.timeSta = time()

    def setTimeSto( self ):
        if ( self.en ):
            self.timeSto = time()

    def reportTimeRel( self, msg ):  # print relative time to the previous start
        if ( self.en ):
            print( "%s : %0.2f s" % ( msg, self.timeSto - self.timeSta ) )

    def reportTimeAbs( self, msg ):
        if ( self.en ):
            print( "%s : %0.2f s" % ( msg, self.timeSto - self.timeInit ) )
