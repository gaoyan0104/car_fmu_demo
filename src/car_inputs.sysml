package CarPipelineDemo {

  package SimulationInputs {

    // Vehicle parameters (minimal set for longitudinal demo)
    part vehicle_A {
      attribute mass_kg = 1650;
      attribute Pmax_W  = 140000;
      attribute CdA     = 0.62;
      attribute Crr     = 0.012;
    }

    // Scenario: 0 to 100 km/h (27.78 m/s)
    part scenario_0_100 {
      attribute v0_mps      = 0.0;
      attribute vTarget_mps = 27.78;
      attribute tMax_s      = 30.0;
    }

    // Requirement threshold
    requirement REQ_ACC_001 {
      attribute limit_s = 10.0;
    }
  }
}
