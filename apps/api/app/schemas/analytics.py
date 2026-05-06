from __future__ import annotations

from pydantic import BaseModel


class PlatformBucket(BaseModel):
    posts: int
    views: int
    likes: int
    comments: int
    shares: int
    metrics_source: str
    metrics_note: str | None = None
    source_breakdown: dict[str, int]


class AnalyticsOverview(BaseModel):
    total_posts: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    engagement_rate: float
    by_platform: dict[str, PlatformBucket]


class AnalyticsTimePoint(BaseModel):
    date: str
    posts: int
    views: int
    likes: int
    comments: int
    shares: int


class TopPost(BaseModel):
    post_id: str
    publication_id: str
    provider: str
    title: str
    external_post_id: str | None
    views: int
    likes: int
    comments: int
    shares: int
    engagement: int
    published_at: str | None


class OptimalCell(BaseModel):
    weekday: int
    hour: int
    posts: int
    avg_engagement: float
    views: int


class OptimalTimes(BaseModel):
    cells: list[OptimalCell]
    best: list[OptimalCell]


class InsightsOut(BaseModel):
    summary: str
    recommendations: list[str]
    snapshot: AnalyticsOverview
    optimal: OptimalTimes
    top_posts: list[TopPost]


class SnapshotResult(BaseModel):
    inserted: int
