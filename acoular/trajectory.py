# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2021, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements the definition of trajectories.

.. autosummary::
    :toctree: generated/

    Trajectory
    CircleTrajectory
"""

# imports from other packages
from numpy import array, arange, sort, r_ ,float64, pi,cos,sin,append
from scipy.interpolate import splprep, splev
from traits.api import HasPrivateTraits, Float, Int, \
Property, cached_property, property_depends_on, Dict, Tuple ,CArray

# acoular imports
from .internal import digest


class Trajectory( HasPrivateTraits ):
    """
    Describes a trajectory from sampled points.
    
    Based on a discrete number of points in space and time, a 
    continuous trajectory is calculated using spline interpolation 
    of positions between samples.
    """
    #: Dictionary that assigns discrete time instants (keys) to 
    #: sampled `(x, y, z)` positions along the trajectory (values).
    points = Dict(key_trait = Float, value_trait = Tuple(Float, Float, Float), 
        desc = "sampled positions along the trajectory")
    
    #: Tuple of the start and end time, is set automatically 
    #: (depending on :attr:`points`).
    interval = Property()
    #t_min, t_max tuple
    
    #: Spline data, internal use.
    tck = Property()
    
    # internal identifier
    digest = Property( 
        depends_on = ['points[]'], 
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)
        
    @property_depends_on('points[]')
    def _get_interval( self ):
        return sort(list(self.points.keys()))[r_[0, -1]]

    @property_depends_on('points[]')
    def _get_tck( self ):
        t = sort(list(self.points.keys()))
        xp = array([self.points[i] for i in t]).T
        k = min(3, len(self.points)-1)
        tcku = splprep(xp, u=t, s=0, k=k)
        return tcku[0]
    
    def location(self, t, der=0):
        """ 
        Returns the positions for one or more instants in time.
        
        Parameters
        ----------
        t : array of floats
            Instances in time to calculate the positions at.
        der : integer
            The order of derivative of the spline to compute, defaults to 0.
        
        Returns
        -------
        (x, y, z) : tuple with arrays of floats
            Positions at the given times; `x`, `y` and `z` have the same shape as `t`.
        """
        return splev(t, self.tck, der)
    
    def traj(self, t_start, t_end=None, delta_t=None, der=0):
        """
        Python generator that yields locations along the trajectory.
        
        Parameters
        ----------
        t_start : float
            Starting time of the trajectory, defaults to the earliest  
            time in :attr:`points`.
        t_end : float
            Ending time of the trajectory, defaults to the latest  
            time in :attr:`points`.
        delta_t : float
            Time interval between yielded trajectory points, defaults to earliest  
            time in :attr:`points`.
        
        Returns
        -------
        (x, y, z) : tuples of floats
            Positions at the desired times are yielded.
            
        Examples
        --------
        x.traj(0.1)  
            Yields the position every 0.1 s within the 
            given :attr:`interval`.
        x.traj(2.5, 4.5, 0.1)  
            Yields the position every 0.1 s between 2.5 s and 4.5 s.
        x.traj(0.1, der=1)  
            Yields the 1st derivative of the spline (= velocity vector) every 0.1 s 
            within the given :attr:`interval`.
        """
        if not delta_t:
            delta_t = t_start
            t_start, t_end = self.interval
        if not t_end:
            t_end = self.interval[1]
        # all locations are fetched in one go because thats much faster
        # further improvement could be possible if interpolated locations are fetched
        # in blocks
        for l in zip(*self.location(arange(t_start, t_end, delta_t),der)):
            yield l
        
        
class CircleTrajectory( Trajectory ):
    """
    Describes a circle trajectory from sampled points.
    
    Based on a discrete number of points in space and time, a 
    continuous trajectory is calculated using spline interpolation 
    of positions between samples.
    """
    
    points = Property()
    
    points_ = Dict(key_trait = Float, value_trait = Tuple(Float, Float, Float), 
        desc = "sampled positions along the trajectory")
    
    #: rpm of the source on the circle"
    rpm = Float(0,
        desc = "rpm of the source on the circle")
    
    #: center of rotation
    origin = CArray( dtype=float64, shape=(3, ), value=array((0., 0., 0.)), 
        desc="center of rotation")
    
    
    #: distance of the source from the center of rotation
    radius = Float(0,
        desc = "distance of the source from the center of rotation")
    
    #: distance of the source from the center of rotation
    start_angle = Float(0,
        desc = "Angle of the source at the start of the trajectory")
    
    points_per_revolution = Int(16,
        desc = "distance of the source from the center of rotation")
    
    rotation_time = Float(1,
        desc = "Time of the roatation in s")
    
    #: Tuple of the start and end time, is set automatically 
    #: (depending on :attr:`points`).
    interval = Property()
    #t_min, t_max tuple
    
    # internal identifier
    digest = Property( 
        depends_on = ['rpm','radius','origin','start_angle','points_per_revolution','rotation_time'], 
        )

    @cached_property
    def _get_digest( self ):
        return digest(self)
    

    @property_depends_on(['rpm','radius','origin','start_angle','points_per_revolution','rotation_time'])
    def _get_points( self ):
        pnts = {}
        for t in arange (0 , self.rotation_time*1.001 , 1./ abs(self.rpm/60 )/self.points_per_revolution):
            phi = t *  self.rpm/60 * 2 * pi # angle
            pnts[t] = ( self.radius * cos( phi + self.start_angle )+self.origin[0],\
                         self.radius  * sin ( phi + self.start_angle )+self.origin[1]  , self.origin[2] )

        return pnts
    
    def _set_points( self, pointdict ):
        self._points= pointdict
    
    
    
    


