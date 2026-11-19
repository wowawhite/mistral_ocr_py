# Implementation notes

This update is based on the uploaded repository snapshot, not a live GitHub checkout.

## Implemented
- GUI and CLI now call the same `process_batch()` service.
- Processing failures are retained as rows with `status=failed`, zero quality score and an error message.
- Source images are no longer moved automatically.
- AI quality score is explicitly described as heuristic, not calibrated probability.
- `Geprüft` starts empty and is only set by the GUI checkbox.
- Reviewed records are revalidated before export; invalid reviewed rows block export.
- OCR retries and timeout are configurable via environment variables.
- Excel exports include status/error fields and a statistics worksheet.
- OCR-controlled text is escaped before writing to cells.
- Pydantic mutable defaults use `default_factory`; count/confidence constraints are explicit.
- Initial offline unit tests cover validation, schemas, confidence and export behavior.

## Not claimed / follow-up work
- No real handwriting dataset was provided, so OCR accuracy and confidence calibration have not been measured.
- No live Ollama integration test was run.
- Duplicate-document detection and safe reprocessing identifiers are not implemented.
- Audit trail currently preserves the initial OCR values in the in-memory evaluation during a GUI session; persistent correction history is not yet stored in a separate database.
- Image size/pixel limits and content-type hardening should be added before processing untrusted uploads at scale.
