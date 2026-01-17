within ;
model LongitudinalVehicle
  parameter Real m = 1650 "vehicle mass [kg]";
  parameter Real Pmax = 140000 "max power [W]";
  parameter Real CdA = 0.62 "aero drag area [m2]";
  parameter Real Crr = 0.012 "rolling resistance coefficient";
  parameter Real v0 = 0.0 "initial speed [m/s]";
  parameter Real vTarget = 27.78 "target speed [m/s]";
  parameter Real tMax = 30.0 "max sim time [s]";

  parameter Real g = 9.81;
  parameter Real rho = 1.225;
  parameter Real Fmax = 8000.0 "traction force limit [N]";
  parameter Real eps = 0.5 "avoid division by zero [m/s]";

  Real v(start=v0) "vehicle speed [m/s]";
  Real a "acceleration [m/s2]";
  Real F_trac "traction force [N]";
  Real F_roll "rolling resistance [N]";
  Real F_aero "aero drag [N]";

equation
  F_roll = m*g*Crr;
  F_aero = 0.5*rho*CdA*v*v;
  F_trac = min(Fmax, Pmax/max(v, eps));
  a = max(0.0, (F_trac - F_roll - F_aero)/m);
  der(v) = a;
end LongitudinalVehicle;
