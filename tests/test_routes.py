import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application instance for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoints:
    """Test health and info endpoints."""
    
    def test_home_endpoint(self, client):
        """Test home endpoint returns API info."""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert 'endpoints' in data
        assert 'version' in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['dataset_loaded'] is True
        assert 'records_count' in data
    
    def test_stats_endpoint(self, client):
        """Test stats endpoint returns dataset statistics."""
        response = client.get('/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_titles' in data
        assert 'movies' in data
        assert 'tv_shows' in data
        assert data['total_titles'] > 0


class TestSearchValidation:
    """Test search parameter validation."""
    
    def test_search_no_params(self, client):
        """Test search without any parameters returns error."""
        response = client.get('/search')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error'].lower()
    
    def test_search_invalid_param(self, client):
        """Test search with invalid parameter."""
        response = client.get('/search?invalid=test')
        assert response.status_code == 400
        data = response.get_json()
        assert 'Unsupported' in data['error']
    
    def test_search_empty_param(self, client):
        """Test search with empty parameter."""
        response = client.get('/search?actor=')
        assert response.status_code == 400
    
    def test_search_long_param(self, client):
        """Test search with overly long parameter."""
        long_string = 'a' * 150
        response = client.get(f'/search?actor={long_string}')
        assert response.status_code == 400
        data = response.get_json()
        assert 'exceeds maximum length' in data['error'].lower()


class TestSearchFunctionality:
    """Test search endpoint functionality."""
    
    def test_search_by_actor(self, client):
        """Test search by actor returns results."""
        response = client.get('/search?actor=Tom')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert 'total' in data
        assert 'page' in data
        assert isinstance(data['results'], list)
    
    def test_search_by_director(self, client):
        """Test search by director."""
        response = client.get('/search?director=Martin')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
    
    def test_search_by_genre(self, client):
        """Test search by genre."""
        response = client.get('/search?genre=Comedy')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['total'] >= 0
    
    def test_search_combined_filters(self, client):
        """Test search with multiple filters."""
        response = client.get('/search?actor=Tom&genre=Drama')
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
    
    def test_search_case_insensitive(self, client):
        """Test search is case-insensitive."""
        response1 = client.get('/search?actor=tom')
        response2 = client.get('/search?actor=TOM')
        response3 = client.get('/search?actor=Tom')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # All should return same results
        data1 = response1.get_json()
        data2 = response2.get_json()
        data3 = response3.get_json()
        
        assert data1['total'] == data2['total'] == data3['total']
    
    def test_search_no_results(self, client):
        """Test search with no matching results."""
        response = client.get('/search?actor=ZZZNonexistentActor999')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 0
        assert len(data['results']) == 0


class TestPagination:
    """Test pagination functionality."""
    
    def test_default_pagination(self, client):
        """Test default pagination values."""
        response = client.get('/search?genre=Drama')
        assert response.status_code == 200
        data = response.get_json()
        assert data['page'] == 1
        assert data['limit'] == 20
        assert 'pages' in data
    
    def test_custom_page(self, client):
        """Test custom page parameter."""
        response = client.get('/search?genre=Drama&page=2')
        assert response.status_code == 200
        data = response.get_json()
        assert data['page'] == 2
    
    def test_custom_limit(self, client):
        """Test custom limit parameter."""
        response = client.get('/search?genre=Drama&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert data['limit'] == 10
        assert len(data['results']) <= 10
    
    def test_invalid_page(self, client):
        """Test invalid page number."""
        response = client.get('/search?genre=Drama&page=0')
        assert response.status_code == 400
    
    def test_invalid_limit(self, client):
        """Test invalid limit value."""
        response = client.get('/search?genre=Drama&limit=200')
        assert response.status_code == 400
    
    def test_negative_page(self, client):
        """Test negative page number."""
        response = client.get('/search?genre=Drama&page=-1')
        assert response.status_code == 400
    
    def test_non_integer_pagination(self, client):
        """Test non-integer pagination parameters."""
        response = client.get('/search?genre=Drama&page=abc')
        assert response.status_code == 400


class TestCaching:
    """Test caching functionality."""
    
    def test_cache_hit(self, client):
        """Test that repeated queries hit the cache."""
        # First request
        response1 = client.get('/search?actor=Tom&page=1&limit=10')
        assert response1.status_code == 200
        
        # Second identical request should hit cache
        response2 = client.get('/search?actor=Tom&page=1&limit=10')
        assert response2.status_code == 200
        
        # Results should be identical
        assert response1.get_json() == response2.get_json()
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns cache statistics."""
        # Make some requests first
        client.get('/search?actor=Tom')
        client.get('/search?actor=Tom')  # Cache hit
        client.get('/search?director=Martin')  # Cache miss
        
        response = client.get('/metrics')
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'cache' in data
        assert 'hits' in data['cache']
        assert 'misses' in data['cache']
        assert 'hit_rate' in data['cache']
        assert data['cache']['hits'] >= 0
        assert data['cache']['misses'] >= 0


class TestResponseFormat:
    """Test response format and structure."""
    
    def test_search_response_structure(self, client):
        """Test search response has correct structure."""
        response = client.get('/search?genre=Drama')
        assert response.status_code == 200
        data = response.get_json()
        
        # Check required keys
        assert 'results' in data
        assert 'total' in data
        assert 'page' in data
        assert 'limit' in data
        assert 'pages' in data
        
        # Check result structure
        if len(data['results']) > 0:
            result = data['results'][0]
            assert 'title' in result
            assert 'type' in result
            assert 'release_year' in result
    
    def test_error_response_structure(self, client):
        """Test error responses have correct structure."""
        response = client.get('/search?invalid=param')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_special_characters_in_search(self, client):
        """Test search with special characters."""
        response = client.get('/search?actor=O%27Brien')  # O'Brien
        assert response.status_code == 200
    
    def test_unicode_in_search(self, client):
        """Test search with unicode characters."""
        response = client.get('/search?actor=José')
        assert response.status_code == 200
    
    def test_whitespace_handling(self, client):
        """Test that whitespace is properly handled."""
        response = client.get('/search?actor=%20%20Tom%20%20')  # "  Tom  "
        # Should either work or return validation error, but not crash
        assert response.status_code in [200, 400]
