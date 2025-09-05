"""
Performance monitoring and optimization for the Jira multi-agent system.
Provides metrics, caching, and performance insights.
"""

import time
import functools
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os


class PerformanceMetrics:
    """Collects and manages performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.agent_stats = defaultdict(lambda: {
            "call_count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "error_count": 0
        })
        self.tool_stats = defaultdict(lambda: {
            "call_count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        })
        self.workflow_stats = defaultdict(lambda: {
            "executions": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "success_rate": 0.0,
            "step_times": []
        })
        self.system_stats = {
            "start_time": datetime.now(),
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        self._lock = threading.Lock()
    
    def record_agent_call(self, agent_name: str, execution_time: float, success: bool = True):
        """Record an agent call performance metric."""
        with self._lock:
            stats = self.agent_stats[agent_name]
            stats["call_count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["call_count"]
            stats["min_time"] = min(stats["min_time"], execution_time)
            stats["max_time"] = max(stats["max_time"], execution_time)
            
            if not success:
                stats["error_count"] += 1
            
            # Keep recent metrics for trending
            self.metrics[f"{agent_name}_times"].append({
                "timestamp": datetime.now(),
                "execution_time": execution_time,
                "success": success
            })
    
    def record_tool_call(self, tool_name: str, execution_time: float, cache_hit: bool = False):
        """Record a tool call performance metric."""
        with self._lock:
            stats = self.tool_stats[tool_name]
            stats["call_count"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["call_count"]
            
            if cache_hit:
                stats["cache_hits"] += 1
            else:
                stats["cache_misses"] += 1
    
    def record_workflow_execution(self, workflow_name: str, execution_time: float, 
                                 step_times: List[float], success: bool = True):
        """Record a workflow execution performance metric."""
        with self._lock:
            stats = self.workflow_stats[workflow_name]
            stats["executions"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["executions"]
            stats["step_times"].extend(step_times)
            
            # Calculate success rate
            if success:
                stats["success_rate"] = (stats["success_rate"] * (stats["executions"] - 1) + 1.0) / stats["executions"]
            else:
                stats["success_rate"] = (stats["success_rate"] * (stats["executions"] - 1)) / stats["executions"]
    
    def record_system_request(self, success: bool = True):
        """Record a system-level request."""
        with self._lock:
            self.system_stats["total_requests"] += 1
            if success:
                self.system_stats["successful_requests"] += 1
            else:
                self.system_stats["failed_requests"] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        with self._lock:
            uptime = datetime.now() - self.system_stats["start_time"]
            
            summary = {
                "system": {
                    "uptime_seconds": uptime.total_seconds(),
                    "total_requests": self.system_stats["total_requests"],
                    "success_rate": (
                        self.system_stats["successful_requests"] / max(1, self.system_stats["total_requests"])
                    ),
                    "requests_per_minute": (
                        self.system_stats["total_requests"] / max(1, uptime.total_seconds() / 60)
                    )
                },
                "agents": dict(self.agent_stats),
                "tools": dict(self.tool_stats),
                "workflows": dict(self.workflow_stats)
            }
            
            return summary
    
    def get_top_performers(self, metric: str = "avg_time", limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents by specified metric."""
        with self._lock:
            if metric == "avg_time":
                sorted_agents = sorted(
                    self.agent_stats.items(),
                    key=lambda x: x[1]["avg_time"]
                )[:limit]
            elif metric == "call_count":
                sorted_agents = sorted(
                    self.agent_stats.items(),
                    key=lambda x: x[1]["call_count"],
                    reverse=True
                )[:limit]
            else:
                return []
            
            return [{"agent": name, **stats} for name, stats in sorted_agents]
    
    def export_metrics(self, filepath: str):
        """Export metrics to a JSON file."""
        summary = self.get_performance_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)


class SimpleCache:
    """Simple in-memory cache for tool results."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        with self._lock:
            if key not in self.cache:
                return None
            
            # Check TTL
            if time.time() - self.access_times[key] > self.ttl_seconds:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set a value in cache."""
        with self._lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": getattr(self, '_hit_rate', 0.0),
                "ttl_seconds": self.ttl_seconds
            }


# Global instances
performance_metrics = PerformanceMetrics()
tool_cache = SimpleCache(max_size=200, ttl_seconds=600)  # 10 minute TTL


def monitor_performance(agent_name: Optional[str] = None):
    """Decorator to monitor agent/function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                execution_time = time.time() - start_time
                name = agent_name or func.__name__
                performance_metrics.record_agent_call(name, execution_time, success)
                performance_metrics.record_system_request(success)
        
        return wrapper
    return decorator


def cache_tool_result(cache_key_func: Optional[Callable] = None, ttl: Optional[int] = None):
    """Decorator to cache tool results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            start_time = time.time()
            cached_result = tool_cache.get(cache_key)
            
            if cached_result is not None:
                execution_time = time.time() - start_time
                performance_metrics.record_tool_call(func.__name__, execution_time, cache_hit=True)
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                tool_cache.set(cache_key, result)
                execution_time = time.time() - start_time
                performance_metrics.record_tool_call(func.__name__, execution_time, cache_hit=False)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_metrics.record_tool_call(func.__name__, execution_time, cache_hit=False)
                raise
        
        return wrapper
    return decorator


def monitor_workflow(workflow_name: str):
    """Decorator to monitor workflow performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            step_times = []
            success = True
            
            try:
                # If the function has step timing, capture it
                if hasattr(func, '_step_timer'):
                    result = func(*args, **kwargs)
                    step_times = getattr(func, '_step_times', [])
                else:
                    result = func(*args, **kwargs)
                
                return result
            except Exception as e:
                success = False
                raise
            finally:
                execution_time = time.time() - start_time
                performance_metrics.record_workflow_execution(
                    workflow_name, execution_time, step_times, success
                )
        
        return wrapper
    return decorator


class PerformanceReporter:
    """Generates performance reports and insights."""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        summary = self.metrics.get_performance_summary()
        
        report = "# Jira Multi-Agent System Performance Report\n\n"
        
        # System overview
        system = summary["system"]
        uptime_hours = system["uptime_seconds"] / 3600
        report += f"## System Overview\n"
        report += f"- **Uptime:** {uptime_hours:.1f} hours\n"
        report += f"- **Total Requests:** {system['total_requests']}\n"
        report += f"- **Success Rate:** {system['success_rate']:.1%}\n"
        report += f"- **Requests/Minute:** {system['requests_per_minute']:.1f}\n\n"
        
        # Agent performance
        if summary["agents"]:
            report += "## Agent Performance\n"
            sorted_agents = sorted(
                summary["agents"].items(),
                key=lambda x: x[1]["call_count"],
                reverse=True
            )
            
            for agent_name, stats in sorted_agents[:10]:  # Top 10
                report += f"### {agent_name}\n"
                report += f"- **Calls:** {stats['call_count']}\n"
                report += f"- **Avg Time:** {stats['avg_time']:.3f}s\n"
                report += f"- **Min/Max:** {stats['min_time']:.3f}s / {stats['max_time']:.3f}s\n"
                if stats['error_count'] > 0:
                    error_rate = stats['error_count'] / stats['call_count']
                    report += f"- **Error Rate:** {error_rate:.1%}\n"
                report += "\n"
        
        # Tool performance
        if summary["tools"]:
            report += "## Tool Performance\n"
            for tool_name, stats in summary["tools"].items():
                cache_rate = stats['cache_hits'] / max(1, stats['cache_hits'] + stats['cache_misses'])
                report += f"### {tool_name}\n"
                report += f"- **Calls:** {stats['call_count']}\n"
                report += f"- **Avg Time:** {stats['avg_time']:.3f}s\n"
                report += f"- **Cache Hit Rate:** {cache_rate:.1%}\n\n"
        
        # Workflow performance
        if summary["workflows"]:
            report += "## Workflow Performance\n"
            for workflow_name, stats in summary["workflows"].items():
                report += f"### {workflow_name}\n"
                report += f"- **Executions:** {stats['executions']}\n"
                report += f"- **Avg Time:** {stats['avg_time']:.3f}s\n"
                report += f"- **Success Rate:** {stats['success_rate']:.1%}\n\n"
        
        # Performance insights
        report += self._generate_insights(summary)
        
        return report
    
    def _generate_insights(self, summary: Dict[str, Any]) -> str:
        """Generate performance insights and recommendations."""
        insights = "## Performance Insights\n\n"
        
        # System health
        success_rate = summary["system"]["success_rate"]
        if success_rate < 0.95:
            insights += "⚠️ **System success rate is below 95%** - investigate error patterns\n\n"
        elif success_rate > 0.99:
            insights += "✅ **Excellent system reliability** - success rate above 99%\n\n"
        
        # Slow agents
        slow_agents = []
        for agent_name, stats in summary["agents"].items():
            if stats["avg_time"] > 5.0:  # Slower than 5 seconds
                slow_agents.append((agent_name, stats["avg_time"]))
        
        if slow_agents:
            insights += "🐌 **Slow Agents Detected:**\n"
            for agent_name, avg_time in sorted(slow_agents, key=lambda x: x[1], reverse=True):
                insights += f"- {agent_name}: {avg_time:.2f}s average\n"
            insights += "\n"
        
        # Cache effectiveness
        cache_stats = tool_cache.stats()
        if cache_stats["size"] > 0:
            insights += f"💾 **Cache Status:** {cache_stats['size']}/{cache_stats['max_size']} entries\n\n"
        
        # Recommendations
        insights += "## Recommendations\n\n"
        
        if slow_agents:
            insights += "1. **Optimize slow agents** - Consider breaking down complex operations\n"
        
        if summary["system"]["requests_per_minute"] > 100:
            insights += "2. **High load detected** - Consider implementing request throttling\n"
        
        insights += "3. **Monitor regularly** - Set up automated performance alerts\n"
        insights += "4. **Cache optimization** - Increase cache size for frequently used tools\n"
        
        return insights
    
    def export_report(self, filepath: str):
        """Export performance report to file."""
        report = self.generate_performance_report()
        with open(filepath, 'w') as f:
            f.write(report)


# Global performance reporter
performance_reporter = PerformanceReporter(performance_metrics)


def get_system_health() -> Dict[str, Any]:
    """Get current system health status."""
    summary = performance_metrics.get_performance_summary()
    cache_stats = tool_cache.stats()
    
    health = {
        "status": "healthy",
        "uptime_hours": summary["system"]["uptime_seconds"] / 3600,
        "success_rate": summary["system"]["success_rate"],
        "total_requests": summary["system"]["total_requests"],
        "cache_utilization": cache_stats["size"] / cache_stats["max_size"],
        "active_agents": len(summary["agents"]),
        "performance_score": min(100, summary["system"]["success_rate"] * 100)
    }
    
    # Determine overall health status
    if health["success_rate"] < 0.9:
        health["status"] = "unhealthy"
    elif health["success_rate"] < 0.95:
        health["status"] = "degraded"
    
    return health
