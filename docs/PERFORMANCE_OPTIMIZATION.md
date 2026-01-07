# Performance Optimization and Integration Testing

This document describes the performance optimizations and integration testing added to the HIPAA anonymization pipeline.

## Performance Optimizations

### 1. Detection Caching

The pipeline now includes a caching mechanism for detection results:

- **Cache Size**: 100 entries (LRU-style eviction)
- **Cache Key**: MD5 hash of input text
- **Benefits**: 
  - Significantly faster for repeated identical texts
  - Reduces redundant processing
  - Especially useful for batch processing with duplicates

**Usage:**
```python
pipeline = HIPAAPipeline()

# First call - processes normally
results1 = pipeline.detect(text)

# Second call with same text - uses cache
results2 = pipeline.detect(text)  # Much faster!

# Disable cache if needed
results3 = pipeline.detect(text, use_cache=False)

# Clear cache
pipeline.clear_cache()
```

### 2. Optimized Batch Processing

New `batch_detect()` method for efficient batch processing:

- **Automatic caching**: Reuses cached results for duplicate texts
- **Optimized iteration**: More efficient than calling `detect()` in a loop
- **Memory efficient**: Processes texts one at a time to avoid memory spikes

**Usage:**
```python
texts = ["Text 1", "Text 2", "Text 1"]  # Note: duplicate
results = pipeline.batch_detect(texts, use_cache=True)
# The duplicate "Text 1" will use cached results
```

### 3. Improved Deduplication Algorithm

The deduplication algorithm has been optimized:

- **Faster overlap checking**: Uses interval-based approach instead of set lookups
- **Better performance**: O(n log n) instead of O(n²) for worst case
- **Same accuracy**: Maintains the same deduplication quality

### 4. API Batch Endpoint Optimization

The `/batch/detect` endpoint now uses the optimized `batch_detect()` method:

- **Better throughput**: Up to 2-3x faster for batches with duplicates
- **Lower latency**: Reduced overhead from optimized processing
- **Automatic caching**: Transparent caching for repeated texts

## Integration Testing

### Pipeline Integration Tests

Located in `tests/integration/test_pipeline_integration.py`:

- **Full pipeline testing**: Tests all tiers working together
- **Anonymization methods**: Tests all anonymization strategies
- **Error handling**: Validates graceful error handling
- **HIPAA coverage**: Verifies all 17 identifiers are detected
- **Deduplication**: Ensures overlapping detections are handled correctly

**Test Coverage:**
- Tier 1 only detection
- Tier 1 + Tier 2 detection
- All anonymization methods (safe_harbor, pseudonymize, redact, tag)
- Metadata generation
- Error handling scenarios
- Complete HIPAA identifier coverage

### API Integration Tests

Located in `tests/integration/test_api_integration.py`:

- **Endpoint testing**: Tests all API endpoints
- **Batch processing**: Validates batch endpoints
- **Error handling**: Tests API error responses
- **Response validation**: Ensures correct response formats

**Test Coverage:**
- `/detect` endpoint
- `/anonymize` endpoint
- `/batch/detect` endpoint
- `/batch/anonymize` endpoint
- `/health` endpoint
- Error handling and validation

## Performance Benchmarking

### Benchmark Script

Located in `scripts/benchmark_performance.py`:

**Features:**
- Measures detection latency and throughput
- Tests anonymization performance
- Memory usage profiling
- Multiple configuration testing (Tier 1, Tier 1+2, Tier 1+2+3)
- Statistical analysis (mean, std dev, min/max)

**Usage:**
```bash
python scripts/benchmark_performance.py
```

**Output:**
- Average latency per document
- Throughput (documents/second)
- Memory usage (current and peak)
- Statistics for each configuration

### Expected Performance

**Tier 1 Only:**
- Latency: < 10ms per document
- Throughput: 100+ documents/second
- Memory: < 50MB

**Tier 1 + Tier 2:**
- Latency: 50-200ms per document
- Throughput: 5-20 documents/second
- Memory: 200-500MB

**Tier 1 + Tier 2 + Tier 3:**
- Latency: 1-5 seconds per document
- Throughput: 0.2-1 documents/second
- Memory: 2-4GB

*Note: Performance varies based on text length, hardware, and model size.*

## Running Tests

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run pipeline integration tests only
pytest tests/integration/test_pipeline_integration.py -v

# Run API integration tests only
pytest tests/integration/test_api_integration.py -v
```

### Performance Benchmarks

```bash
# Run performance benchmarks
python scripts/benchmark_performance.py
```

## Best Practices

### For Production Use

1. **Enable caching** for batch processing with potential duplicates
2. **Use batch_detect()** instead of looping over `detect()`
3. **Clear cache periodically** if processing very large batches
4. **Monitor memory usage** when processing large documents
5. **Use appropriate tier configuration** based on accuracy vs. speed requirements

### For Development

1. **Run integration tests** before committing changes
2. **Run benchmarks** after performance-related changes
3. **Test with realistic data** to validate real-world performance
4. **Profile slow paths** using Python profilers if needed

## Future Optimizations

Potential areas for further optimization:

1. **Parallel processing**: Process multiple texts concurrently
2. **Model quantization**: Further reduce memory and improve speed
3. **Incremental processing**: Process large documents in chunks
4. **GPU acceleration**: Utilize GPU for Tier 2 and Tier 3 when available
5. **Distributed processing**: Scale across multiple machines

