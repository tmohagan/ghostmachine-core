from locust import HttpUser, task, between

class BaselineTraffic(HttpUser):
    """Generates standard synthetic HTTP load against the target."""
    wait_time = between(1, 3)

    @task(3)
    def view_profile(self):
        self.client.get("/api/routes/profile")

class AdversarialFuzzer(HttpUser):
    """Generates malformed payloads to trigger 15 predefined failure scenarios."""
    wait_time = between(2, 5)

    @task(1)
    def trigger_schema_violation(self):
        # Target: Schema Violations (unhandled null fields in comment inputs)
        headers = {"Content-Type": "application/json"}
        bad_payload = {"author": "fuzzer", "content": None} 
        
        with self.client.post("/api/routes/comments", json=bad_payload, headers=headers, catch_response=True) as response:
            # In adversarial fuzzing, receiving a 5xx error is a successful trigger of the control plane
            if response.status_code >= 500:
                response.success()
