concrete UnescoPilotFre of UnescoPilot = {
  flags unlexer = text ;
  lincat Output = {s : Str} ;
  lin RealizeTransitive agent predicate patient = {
    s = agent.s ++ predicate.s ++ patient.s ++ "."
  } ;
}
