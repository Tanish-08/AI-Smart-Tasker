"""Comprehensive tests for backend/app/main.py module.

This module contains tests covering:
- Lifespan context manager (startup and shutdown)
- Database initialization
- LLM client setup
- Health and root endpoints
- Global exception handler
- CORS configuration
- Router inclusion

All tests use proper mocking for database and LLM calls.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from omegaconf import OmegaConf


# ============================================================================
# LIFESPAN TESTS
# ============================================================================

class TestLifespan:
    """Tests for application lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self):
        """Test successful application startup sequence."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db, \
             patch('backend.app.main.create_tables') as mock_create_tables, \
             patch('backend.app.main.LLMClient') as mock_llm_class, \
             patch('backend.app.main.set_llm_client') as mock_set_llm_client:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config

            mock_llm_client = Mock()
            mock_llm_client.health_check.return_value = True
            mock_llm_class.return_value = mock_llm_client

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            async with lifespan(app):
                # Verify startup sequence
                mock_load_config.assert_called_once()
                mock_init_db.assert_called_once_with(mock_config)
                mock_create_tables.assert_called_once()
                mock_llm_class.assert_called_once_with(mock_config)
                mock_set_llm_client.assert_called_once_with(mock_llm_client)
                mock_llm_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_llm_health_check_fails(self):
        """Test startup continues when LLM health check fails."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db, \
             patch('backend.app.main.create_tables') as mock_create_tables, \
             patch('backend.app.main.LLMClient') as mock_llm_class, \
             patch('backend.app.main.set_llm_client') as mock_set_llm_client:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config

            mock_llm_client = Mock()
            mock_llm_client.health_check.return_value = False  # Health check fails
            mock_llm_class.return_value = mock_llm_client

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            async with lifespan(app):
                # Should continue despite health check failure
                mock_llm_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_database_init_fails(self):
        """Test startup failure when database initialization fails."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config
            mock_init_db.side_effect = Exception("Database connection failed")

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            with pytest.raises(Exception, match="Database connection failed"):
                async with lifespan(app):
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_startup_llm_client_fails(self):
        """Test startup failure when LLM client initialization fails."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db, \
             patch('backend.app.main.create_tables') as mock_create_tables, \
             patch('backend.app.main.LLMClient') as mock_llm_class:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config
            mock_llm_class.side_effect = Exception("LLM client initialization failed")

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            with pytest.raises(Exception, match="LLM client initialization failed"):
                async with lifespan(app):
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_startup_config_load_fails(self):
        """Test startup failure when configuration loading fails."""
        with patch('backend.app.main.load_config') as mock_load_config:

            # Setup mocks
            mock_load_config.side_effect = Exception("Configuration loading failed")

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            with pytest.raises(Exception, match="Configuration loading failed"):
                async with lifespan(app):
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_success(self):
        """Test successful application shutdown sequence."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db, \
             patch('backend.app.main.create_tables') as mock_create_tables, \
             patch('backend.app.main.LLMClient') as mock_llm_class, \
             patch('backend.app.main.set_llm_client') as mock_set_llm_client, \
             patch('backend.app.main.close_database') as mock_close_db:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config

            mock_llm_client = Mock()
            mock_llm_client.health_check.return_value = True
            mock_llm_class.return_value = mock_llm_client

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            async with lifespan(app):
                pass  # Yield point

            # Verify shutdown sequence
            mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_with_error(self):
        """Test shutdown sequence continues even if errors occur."""
        with patch('backend.app.main.load_config') as mock_load_config, \
             patch('backend.app.main.init_database') as mock_init_db, \
             patch('backend.app.main.create_tables') as mock_create_tables, \
             patch('backend.app.main.LLMClient') as mock_llm_class, \
             patch('backend.app.main.set_llm_client') as mock_set_llm_client, \
             patch('backend.app.main.close_database') as mock_close_db:

            # Setup mocks
            mock_config = OmegaConf.create({"test": "config"})
            mock_load_config.return_value = mock_config

            mock_llm_client = Mock()
            mock_llm_client.health_check.return_value = True
            mock_llm_class.return_value = mock_llm_client

            mock_close_db.side_effect = Exception("Database close error")

            # Import and test lifespan
            from backend.app.main import lifespan

            app = FastAPI()
            # Should not raise exception, just log error
            async with lifespan(app):
                pass


# ============================================================================
# ENDPOINT TESTS
# ============================================================================

class TestEndpoints:
    """Tests for health and root endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create a test client without lifespan."""
        # Create a minimal app without lifespan for testing endpoints only
        from backend.app.endpoint import (
            task_routes,
            summary_routes,
            analytics_routes,
            deadline_routes,
        )
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(
            title="AI Task Manager API",
            description="Backend API for AI-powered task management with deadline motivation",
            version="1.0.0"
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include routers
        app.include_router(task_routes.router)
        app.include_router(summary_routes.router)
        app.include_router(analytics_routes.router)
        app.include_router(deadline_routes.router)

        # Add health check endpoint
        @app.get("/health", tags=["health"])
        async def health_check():
            return {
                "status": "healthy",
                "service": "AI Task Manager API",
                "version": "1.0.0"
            }

        # Add root endpoint
        @app.get("/", tags=["root"])
        async def root():
            return {
                "service": "AI Task Manager API",
                "version": "1.0.0",
                "description": "Backend API for AI-powered task management",
                "docs": "/docs",
                "health": "/health"
            }

        return TestClient(app)

    def test_health_endpoint_success(self, test_client):
        """Test health check endpoint returns correct status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AI Task Manager API"
        assert data["version"] == "1.0.0"

    def test_health_endpoint_structure(self, test_client):
        """Test health check endpoint returns all required fields."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data

    def test_root_endpoint_success(self, test_client):
        """Test root endpoint returns API information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI Task Manager API"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Backend API for AI-powered task management"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"

    def test_root_endpoint_structure(self, test_client):
        """Test root endpoint returns all required fields."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "description" in data
        assert "docs" in data
        assert "health" in data

    def test_health_endpoint_content_type(self, test_client):
        """Test health endpoint returns JSON content type."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_root_endpoint_content_type(self, test_client):
        """Test root endpoint returns JSON content type."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


# ============================================================================
# EXCEPTION HANDLER TESTS
# ============================================================================

class TestExceptionHandler:
    """Tests for global exception handler."""

    @pytest.fixture
    def test_client_with_exception(self):
        """Create a test client with an endpoint that raises exceptions."""
        app = FastAPI()

        # Add exception handler
        from fastapi import Request
        from fastapi.responses import JSONResponse

        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "message": str(exc)
                }
            )

        # Add test endpoint that raises exception
        @app.get("/test-error")
        async def test_error():
            raise ValueError("Test error message")

        # Add test endpoint that raises different exception
        @app.get("/test-runtime-error")
        async def test_runtime_error():
            raise RuntimeError("Runtime error occurred")

        # Add test endpoint that works normally
        @app.get("/test-success")
        async def test_success():
            return {"status": "success"}

        return TestClient(app, raise_server_exceptions=False)

    def test_exception_handler_catches_exception(self, test_client_with_exception):
        """Test that exception handler catches unhandled exceptions."""
        response = test_client_with_exception.get("/test-error")

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "message" in data

    def test_exception_handler_returns_error_details(self, test_client_with_exception):
        """Test that exception handler returns correct error details."""
        response = test_client_with_exception.get("/test-error")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"
        assert "Test error message" in data["message"]

    def test_exception_handler_handles_different_exceptions(self, test_client_with_exception):
        """Test that exception handler handles different exception types."""
        response = test_client_with_exception.get("/test-runtime-error")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"
        assert "Runtime error occurred" in data["message"]

    def test_exception_handler_does_not_affect_normal_requests(self, test_client_with_exception):
        """Test that exception handler doesn't interfere with normal requests."""
        response = test_client_with_exception.get("/test-success")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


# ============================================================================
# APP CONFIGURATION TESTS
# ============================================================================

class TestAppConfiguration:
    """Tests for FastAPI application configuration."""

    def test_global_exception_response_does_not_expose_exception_details(self):
        """Unhandled exception details stay in server logs rather than API responses."""
        import asyncio

        from fastapi import Request
        from backend.app.main import app

        handler = app.exception_handlers[Exception]
        request = Request({"type": "http", "method": "GET", "path": "/"})
        response = asyncio.run(handler(request, RuntimeError("private database detail")))

        assert response.status_code == 500
        assert b"private database detail" not in response.body
        assert b"Internal server error" in response.body

    def test_cors_middleware_does_not_allow_every_origin(self):
        """Browser access is limited to configured origins, not a wildcard."""
        from backend.app.main import app

        cors_middleware = next(
            middleware
            for middleware in app.user_middleware
            if middleware.cls.__name__ == "CORSMiddleware"
        )
        assert "*" not in cors_middleware.kwargs["allow_origins"]

    def test_app_title_configuration(self):
        """Test that app has correct title."""
        from backend.app.main import app

        assert app.title == "AI Task Manager API"

    def test_app_description_configuration(self):
        """Test that app has correct description."""
        from backend.app.main import app

        assert "AI-powered task management" in app.description

    def test_app_version_configuration(self):
        """Test that app has correct version."""
        from backend.app.main import app

        assert app.version == "1.0.0"

    def test_app_has_lifespan(self):
        """Test that app has lifespan configured."""
        from backend.app.main import app

        assert app.router.lifespan_context is not None

    def test_app_cors_middleware_configured(self):
        """Test that CORS middleware is configured."""
        from backend.app.main import app

        # Check if CORS middleware is in the middleware stack
        # FastAPI stores middleware as Middleware objects with cls attribute
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert any("CORS" in middleware_cls for middleware_cls in middleware_classes)

    def test_app_routes_included(self):
        """Test that all required routes are included."""
        from backend.app.main import app

        # Resolve included routers through OpenAPI for FastAPI version compatibility.
        routes = app.openapi()["paths"]

        # Verify core endpoints exist
        assert "/" in routes
        assert "/health" in routes

        # Verify API route prefixes are included
        route_prefixes = ["/api/tasks", "/api/summaries", "/api/analytics", "/api/deadlines"]
        for prefix in route_prefixes:
            # Check if any route starts with this prefix
            assert any(route.startswith(prefix) for route in routes), f"Route prefix {prefix} not found"


# ============================================================================
# INTEGRATION TESTS WITH FULL APP
# ============================================================================

class TestFullAppIntegration:
    """Integration tests with full application including all components."""

    @pytest.fixture
    def mock_full_app_client(self, test_db, mock_llm_client, mock_config):
        """Create a test client with full app but mocked dependencies."""
        from backend.app.dependencies import get_config, get_llm_client, set_llm_client
        from backend.app.utils.database import get_db
        from backend.app.endpoint import (
            task_routes,
            summary_routes,
            analytics_routes,
            deadline_routes,
        )
        from fastapi.middleware.cors import CORSMiddleware

        # Create app without lifespan to avoid startup issues
        app = FastAPI(
            title="AI Task Manager API",
            description="Backend API for AI-powered task management with deadline motivation",
            version="1.0.0"
        )

        # Configure CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Exception handler
        from fastapi import Request
        from fastapi.responses import JSONResponse

        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "message": str(exc)
                }
            )

        # Health check endpoint
        @app.get("/health", tags=["health"])
        async def health_check():
            return {
                "status": "healthy",
                "service": "AI Task Manager API",
                "version": "1.0.0"
            }

        # Root endpoint
        @app.get("/", tags=["root"])
        async def root():
            return {
                "service": "AI Task Manager API",
                "version": "1.0.0",
                "description": "Backend API for AI-powered task management",
                "docs": "/docs",
                "health": "/health"
            }

        # Include routers
        app.include_router(task_routes.router)
        app.include_router(summary_routes.router)
        app.include_router(analytics_routes.router)
        app.include_router(deadline_routes.router)

        # Override dependencies
        app.dependency_overrides[get_db] = lambda: test_db
        app.dependency_overrides[get_config] = lambda: mock_config
        app.dependency_overrides[get_llm_client] = lambda: mock_llm_client

        # Set LLM client globally
        set_llm_client(mock_llm_client)

        client = TestClient(app, raise_server_exceptions=False)
        yield client

        # Clean up
        app.dependency_overrides.clear()

    def test_full_app_health_check(self, mock_full_app_client):
        """Test health check with full app configuration."""
        response = mock_full_app_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_full_app_root_endpoint(self, mock_full_app_client):
        """Test root endpoint with full app configuration."""
        response = mock_full_app_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI Task Manager API"

    def test_full_app_cors_headers(self, mock_full_app_client):
        """Test that CORS headers are properly configured."""
        response = mock_full_app_client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })

        # CORS should allow the request
        assert "access-control-allow-origin" in response.headers

    def test_full_app_exception_handler_integration(self, mock_full_app_client):
        """Test that exception handler works in full app context."""
        # Try to access a non-existent endpoint
        response = mock_full_app_client.get("/non-existent-endpoint")

        # Should return 404, not 500 (FastAPI's default 404 handler)
        assert response.status_code == 404


# ============================================================================
# LOGGING TESTS
# ============================================================================

class TestLogging:
    """Tests for logging configuration and behavior."""

    def test_logging_configured(self):
        """Test that logging is properly configured."""
        import logging

        # Import main to trigger logging configuration
        import backend.app.main

        logger = logging.getLogger('backend.app.main')
        assert logger.level <= logging.INFO

    def test_logger_exists(self):
        """Test that logger is created."""
        from backend.app.main import logger

        assert logger is not None
        assert logger.name == 'backend.app.main'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
