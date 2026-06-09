# Layout Recovery Models

No current model parameters are tracked here.

Allowed tracked content:

* small metadata summaries
* model cards without parameters
* distilled rule candidates after review

Not allowed:

* checkpoints
* `*.pkl`
* `*.pt`
* `*.onnx`
* `*.safetensors`
* feature matrices
* prediction dumps

Heavy teacher artifacts must remain under ignored `local_only/` paths.
