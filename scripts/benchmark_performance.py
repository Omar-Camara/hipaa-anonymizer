#!/usr/bin/env python3
"""
Performance benchmarking script for HIPAA anonymization pipeline.

Measures throughput, latency, and memory usage for different configurations.
"""

import time
import sys
import statistics
from pathlib import Path
from typing import List, Dict
import tracemalloc

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import HIPAAPipeline


# Sample test texts of varying complexity
SAMPLE_TEXTS = [
    # Simple - single PHI
    "Patient SSN: 123-45-6789",
    
    # Medium - multiple PHI types
    """
    Patient: John Smith
    DOB: 08/20/1955
    SSN: 123-45-6789
    Phone: (555) 123-4567
    Email: john.smith@hospital.com
    Address: 123 Main St, Boston, MA 02118
    """,
    
    # Complex - full medical note
    """
    SURGICAL CONSULTATION NOTE
    
    Patient: Jane Doe
    DOB: 03/15/1978
    MRN: 987654321
    SSN: 987-65-4321
    
    Chief Complaint: Patient presents with abdominal pain.
    
    History of Present Illness:
    The patient is a 45-year-old female who presents to the emergency department
    with complaints of severe abdominal pain that started approximately 6 hours ago.
    The pain is located in the right lower quadrant and is associated with nausea.
    
    Past Medical History:
    - Hypertension
    - Diabetes Type 2
    - Previous appendectomy in 2010
    
    Medications:
    - Lisinopril 10mg daily
    - Metformin 500mg twice daily
    
    Physical Examination:
    Vital signs: BP 140/90, HR 88, RR 18, Temp 98.6F
    Abdomen: Tender in right lower quadrant with guarding.
    
    Assessment and Plan:
    1. Acute appendicitis - rule out
    2. Order CT scan of abdomen
    3. Surgical consultation
    
    Contact Information:
    Phone: (555) 987-6543
    Email: jane.doe@email.com
    Emergency Contact: John Doe, (555) 987-6544
    
    Attending Physician: Dr. Sarah Johnson
    Date: March 20, 2024
    """,
    
    # Very complex - multiple patients, extensive PHI
    """
    CLINICAL SUMMARY - MULTIPLE PATIENTS
    
    Patient 1:
    Name: Robert Williams
    DOB: 11/22/1965
    SSN: 111-22-3333
    MRN: 111222333
    Insurance: Blue Cross, Member ID: BC123456789
    Phone: (555) 111-2222
    Address: 456 Oak Avenue, Los Angeles, CA 90001
    
    Patient 2:
    Name: Maria Garcia
    DOB: 05/14/1982
    SSN: 222-33-4444
    MRN: 222333444
    Insurance: Aetna, Policy #: AET789012345
    Phone: (555) 222-3333
    Email: maria.garcia@email.com
    Address: 789 Pine Street, San Francisco, CA 94102
    
    Patient 3:
    Name: David Chen
    DOB: 09/30/1990
    SSN: 333-44-5555
    MRN: 333444555
    Account #: 444555666
    License: DL-987654321
    Phone: (555) 333-4444
    Address: 321 Elm Drive, San Diego, CA 92101
    
    Clinical Notes:
    All three patients were seen in the outpatient clinic on 04/15/2024.
    Follow-up appointments scheduled for next week.
    
    Contact: clinic@hospital.com
    Fax: (555) 999-8888
    """
]


def benchmark_detection(
    pipeline: HIPAAPipeline,
    texts: List[str],
    iterations: int = 10
) -> Dict:
    """Benchmark detection performance."""
    times = []
    total_detections = 0
    
    for _ in range(iterations):
        start = time.perf_counter()
        for text in texts:
            detections = pipeline.detect(text)
            total_detections += len(detections)
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)
    
    total_texts = len(texts) * iterations
    throughput = total_texts / avg_time
    
    return {
        "avg_latency_ms": avg_time * 1000,
        "std_latency_ms": std_time * 1000,
        "min_latency_ms": min_time * 1000,
        "max_latency_ms": max_time * 1000,
        "throughput_docs_per_sec": throughput,
        "total_detections": total_detections,
        "avg_detections_per_text": total_detections / total_texts
    }


def benchmark_anonymization(
    pipeline: HIPAAPipeline,
    texts: List[str],
    method: str = "safe_harbor",
    iterations: int = 10
) -> Dict:
    """Benchmark anonymization performance."""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        for text in texts:
            _ = pipeline.anonymize(text, method=method)
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    
    total_texts = len(texts) * iterations
    throughput = total_texts / avg_time
    
    return {
        "avg_latency_ms": avg_time * 1000,
        "std_latency_ms": std_time * 1000,
        "throughput_docs_per_sec": throughput
    }


def benchmark_memory(pipeline: HIPAAPipeline, text: str) -> Dict:
    """Benchmark memory usage."""
    tracemalloc.start()
    
    # Warm up
    _ = pipeline.detect(text)
    
    # Measure
    snapshot1 = tracemalloc.take_snapshot()
    _ = pipeline.detect(text)
    snapshot2 = tracemalloc.take_snapshot()
    
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return {
        "current_memory_mb": current / 1024 / 1024,
        "peak_memory_mb": peak / 1024 / 1024
    }


def run_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 80)
    print("HIPAA Anonymization Pipeline - Performance Benchmarks")
    print("=" * 80)
    print()
    
    # Test configurations
    configurations = [
        ("Tier 1 Only", {"enable_tier2": False, "enable_tier3": False}),
        ("Tier 1 + Tier 2", {"enable_tier2": True, "enable_tier3": False}),
        # Note: Tier 3 is slow, so we'll test it separately if available
    ]
    
    for config_name, config in configurations:
        print(f"\n{'=' * 80}")
        print(f"Configuration: {config_name}")
        print(f"{'=' * 80}\n")
        
        try:
            pipeline = HIPAAPipeline(**config)
        except Exception as e:
            print(f"⚠️  Configuration not available: {e}")
            continue
        
        # Detection benchmarks
        print("📊 Detection Performance:")
        print("-" * 80)
        det_results = benchmark_detection(pipeline, SAMPLE_TEXTS, iterations=5)
        print(f"  Average Latency: {det_results['avg_latency_ms']:.2f} ms (±{det_results['std_latency_ms']:.2f})")
        print(f"  Min/Max Latency: {det_results['min_latency_ms']:.2f} / {det_results['max_latency_ms']:.2f} ms")
        print(f"  Throughput: {det_results['throughput_docs_per_sec']:.2f} documents/second")
        print(f"  Average Detections: {det_results['avg_detections_per_text']:.2f} per text")
        print()
        
        # Anonymization benchmarks
        print("📊 Anonymization Performance (Safe Harbor):")
        print("-" * 80)
        anon_results = benchmark_anonymization(pipeline, SAMPLE_TEXTS, method="safe_harbor", iterations=5)
        print(f"  Average Latency: {anon_results['avg_latency_ms']:.2f} ms (±{anon_results['std_latency_ms']:.2f})")
        print(f"  Throughput: {anon_results['throughput_docs_per_sec']:.2f} documents/second")
        print()
        
        # Memory benchmarks
        print("📊 Memory Usage:")
        print("-" * 80)
        mem_results = benchmark_memory(pipeline, SAMPLE_TEXTS[1])
        print(f"  Current Memory: {mem_results['current_memory_mb']:.2f} MB")
        print(f"  Peak Memory: {mem_results['peak_memory_mb']:.2f} MB")
        print()
    
    # Test Tier 3 separately if available
    print(f"\n{'=' * 80}")
    print("Configuration: Tier 1 + Tier 2 + Tier 3 (if available)")
    print(f"{'=' * 80}\n")
    
    try:
        pipeline_tier3 = HIPAAPipeline(enable_tier2=True, enable_tier3=True)
        print("✅ Tier 3 is available")
        
        # Test with single text (Tier 3 is slow)
        print("\n📊 Detection Performance (Tier 3 enabled):")
        print("-" * 80)
        det_results = benchmark_detection(pipeline_tier3, [SAMPLE_TEXTS[1]], iterations=3)
        print(f"  Average Latency: {det_results['avg_latency_ms']:.2f} ms")
        print(f"  Throughput: {det_results['throughput_docs_per_sec']:.2f} documents/second")
        print()
    except Exception as e:
        print(f"⚠️  Tier 3 not available: {e}")
        print("   (This is expected if models are not downloaded)")
    
    print("\n" + "=" * 80)
    print("Benchmark Complete!")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmarks()

