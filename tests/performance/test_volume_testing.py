"""Volume Testing - Test system performance with large amounts of data"""
import pytest
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

class TestVolumeTesting:
    """Volume testing to verify system performance with large datasets"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = "http://localhost:5000"
        self.token = self._get_auth_token()
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
    def _get_auth_token(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/api/login", json={
                "username": "admin",
                "password": "password123"
            }, timeout=5)
            if response.status_code == 200:
                return response.json()['token']
        except:
            pass
        return None
    
    def _create_test_entries(self, count):
        """Create multiple test entries for volume testing"""
        created_entries = []
        batch_size = 10
        
        for i in range(0, count, batch_size):
            batch_end = min(i + batch_size, count)
            batch_entries = []
            
            for j in range(i, batch_end):
                entry_data = {
                    "name": f"Volume Test User {j}",
                    "email": f"volume{j}@test.com",
                    "comment": f"Volume testing entry number {j} with some additional content to make it realistic"
                }
                
                try:
                    response = requests.post(f"{self.base_url}/api/guestbook", 
                                           json=entry_data, headers=self.headers, timeout=10)
                    if response.status_code in [200, 201]:
                        batch_entries.append(response.json())
                except:
                    pass
            
            created_entries.extend(batch_entries)
            time.sleep(0.1)  # Brief pause between batches
        
        return created_entries
    
    def test_large_dataset_retrieval(self):
        """Test retrieving data when database contains large amount of entries"""
        # Create test data
        print("Creating test entries for volume testing...")
        test_entries_count = 100
        created_entries = self._create_test_entries(test_entries_count)
        
        print(f"Created {len(created_entries)} test entries")
        
        # Test retrieval performance with large dataset
        retrieval_times = []
        
        for _ in range(5):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/guestbook", 
                                      headers=self.headers, timeout=15)
                end_time = time.time()
                
                if response.status_code == 200:
                    retrieval_times.append(end_time - start_time)
                    data = response.json()
                    entries_count = len(data.get('entries', []))
                    print(f"Retrieved {entries_count} entries in {end_time - start_time:.3f}s")
            except Exception as e:
                print(f"Retrieval failed: {e}")
        
        # Analyze results
        if retrieval_times:
            avg_retrieval_time = statistics.mean(retrieval_times)
            max_retrieval_time = max(retrieval_times)
            
            print(f"Large Dataset Retrieval Results:")
            print(f"- Average retrieval time: {avg_retrieval_time:.3f}s")
            print(f"- Max retrieval time: {max_retrieval_time:.3f}s")
            
            # Assertions for volume performance
            assert avg_retrieval_time < 5.0, f"Average retrieval time {avg_retrieval_time:.2f}s exceeds 5s"
            assert max_retrieval_time < 10.0, f"Max retrieval time {max_retrieval_time:.2f}s exceeds 10s"
        else:
            pytest.fail("No successful retrievals during volume test")
    
    def test_pagination_with_large_dataset(self):
        """Test pagination performance with large dataset"""
        page_sizes = [10, 25, 50, 100]
        pagination_results = {}
        
        for page_size in page_sizes:
            page_times = []
            
            # Test first 5 pages for each page size
            for page in range(1, 6):
                start_time = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}/api/guestbook?page={page}&limit={page_size}",
                        headers=self.headers, timeout=10
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        page_times.append(end_time - start_time)
                except:
                    pass
            
            if page_times:
                pagination_results[page_size] = {
                    'avg_time': statistics.mean(page_times),
                    'max_time': max(page_times)
                }
        
        # Analyze pagination performance
        print("Pagination Performance with Large Dataset:")
        for page_size, results in pagination_results.items():
            print(f"- Page size {page_size}: avg {results['avg_time']:.3f}s, max {results['max_time']:.3f}s")
            
            # Assertions
            assert results['avg_time'] < 3.0, f"Page size {page_size} avg time {results['avg_time']:.2f}s exceeds 3s"
            assert results['max_time'] < 5.0, f"Page size {page_size} max time {results['max_time']:.2f}s exceeds 5s"
    
    def test_search_performance_large_dataset(self):
        """Test search performance with large dataset"""
        search_terms = ["test", "user", "volume", "entry", "comment"]
        search_results = {}
        
        for term in search_terms:
            search_times = []
            
            for _ in range(3):  # Test each search term 3 times
                start_time = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}/api/guestbook?search={term}",
                        headers=self.headers, timeout=10
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        search_times.append(end_time - start_time)
                        data = response.json()
                        results_count = len(data.get('entries', []))
                except:
                    pass
            
            if search_times:
                search_results[term] = {
                    'avg_time': statistics.mean(search_times),
                    'max_time': max(search_times)
                }
        
        # Analyze search performance
        print("Search Performance with Large Dataset:")
        for term, results in search_results.items():
            print(f"- Search '{term}': avg {results['avg_time']:.3f}s, max {results['max_time']:.3f}s")
            
            # Assertions
            assert results['avg_time'] < 2.0, f"Search '{term}' avg time {results['avg_time']:.2f}s exceeds 2s"
            assert results['max_time'] < 4.0, f"Search '{term}' max time {results['max_time']:.2f}s exceeds 4s"
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        bulk_sizes = [10, 25, 50]
        bulk_results = {}
        
        for bulk_size in bulk_sizes:
            creation_times = []
            
            # Test bulk creation
            start_time = time.time()
            created_count = 0
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i in range(bulk_size):
                    entry_data = {
                        "name": f"Bulk Test User {i}",
                        "email": f"bulk{i}@test.com",
                        "comment": f"Bulk operation test entry {i}"
                    }
                    future = executor.submit(self._create_single_entry, entry_data)
                    futures.append(future)
                
                for future in futures:
                    if future.result():
                        created_count += 1
            
            end_time = time.time()
            total_time = end_time - start_time
            
            bulk_results[bulk_size] = {
                'total_time': total_time,
                'created_count': created_count,
                'rate': created_count / total_time if total_time > 0 else 0
            }
        
        # Analyze bulk operation performance
        print("Bulk Operations Performance:")
        for size, results in bulk_results.items():
            print(f"- Bulk size {size}: {results['created_count']}/{size} created in {results['total_time']:.3f}s ({results['rate']:.2f} entries/sec)")
            
            # Assertions
            assert results['rate'] > 2.0, f"Bulk creation rate {results['rate']:.2f} entries/sec too slow"
    
    def _create_single_entry(self, entry_data):
        """Helper method to create a single entry"""
        try:
            response = requests.post(f"{self.base_url}/api/guestbook", 
                                   json=entry_data, headers=self.headers, timeout=10)
            return response.status_code in [200, 201]
        except:
            return False