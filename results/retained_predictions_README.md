# Retained per-target predictions

No retained per-target prediction CSV was available in the project artifacts
used for this closeout.

Do not generate a replacement file and label it as the original benchmark
output. A common-support comparison can only be added later if the original
per-target predictions are recovered with their provenance.

Ryan's supplied checker expects one row per model/target/condition with columns:

`missingness,observation_id,model,iv,prediction`

Failed predictions must remain explicit as blank/NaN rows rather than being
omitted.
