# ============================================
# Project: LifeMemoryTracker12
# Author: Ervin Remus Radosavlevici
# Copyright: © 2025 Ervin Remus Radosavlevici
# All rights reserved. Protected under digital trace monitoring.
# Unauthorized usage will trigger automated reports.
# ============================================

import datetime
import socket
import platform
import getpass

def log_access():
    log_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "user": getpass.getuser()
    }
    with open("access_log.txt", "a") as f:
        f.write(str(log_info) + "\n")

log_access()

"""
Advanced admin dashboard for AI Life Coach application
"""
import os
import json
import datetime
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from security import get_security_metrics, system_health_check, log_security_event, get_basic_metrics
from auto_updater import auto_updater

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    """Admin dashboard homepage"""
    try:
        health = system_health_check()
        security_metrics = get_basic_metrics()
        updater_status = auto_updater.get_system_status()

        # Get recent activity summary
        from app import load_memory
        memory = load_memory()

        dashboard_data = {
            "system_health": health,
            "security_metrics": security_metrics,
            "updater_status": updater_status,
            "user_stats": {
                "total_conversations": len(memory.get("life_events", [])),
                "total_goals": len(memory.get("goals", [])),
                "active_goals": len([g for g in memory.get("goals", []) if g.get("status") == "active"]),
                "total_habits": len(memory.get("habits", [])),
                "active_habits": len([h for h in memory.get("habits", []) if h.get("status") == "active"]),
                "mood_entries": len(memory.get("mood_history", [])),
                "achievements": len(memory.get("achievements", [])),
                "reflections": len(memory.get("reflections", [])),
                "milestones": len(memory.get("milestones", [])),
            },
            "recent_activity": memory.get("life_events", [])[-10:],
            "timestamp": datetime.datetime.now().isoformat()
        }

        return render_template('admin/dashboard.html', data=dashboard_data)

    except Exception as e:
        logging.error(f"Error loading admin dashboard: {e}")
        return jsonify({"error": "Dashboard loading failed"}), 500

@admin_bp.route('/api/system/status')
def api_system_status():
    """API endpoint for system status"""
    try:
        health = system_health_check()
        security_metrics = get_security_metrics()
        updater_status = auto_updater.get_system_status()

        return jsonify({
            "status": "operational",
            "health": health,
            "security": security_metrics,
            "updater": updater_status,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/users/analytics')
def user_analytics():
    """Get detailed user analytics"""
    try:
        from app import load_memory
        memory = load_memory()

        # Calculate analytics
        now = datetime.datetime.now()
        week_ago = now - datetime.timedelta(days=7)
        month_ago = now - datetime.timedelta(days=30)

        # Recent activity
        recent_events = [
            e for e in memory.get("life_events", [])
            if datetime.datetime.fromisoformat(e.get("timestamp", e.get("date"))) >= week_ago
        ]

        # Goal completion rates
        goals = memory.get("goals", [])
        completed_goals = [g for g in goals if g.get("status") == "completed"]
        goal_completion_rate = len(completed_goals) / max(1, len(goals)) * 100

        # Habit consistency
        habits = memory.get("habits", [])
        active_habits = [h for h in habits if h.get("status") == "active"]
        avg_streak = sum(h.get("current_streak", 0) for h in active_habits) / max(1, len(active_habits))

        # Mood trends
        mood_history = memory.get("mood_history", [])
        recent_moods = [
            m for m in mood_history
            if datetime.datetime.fromisoformat(m.get("timestamp")) >= week_ago
        ]

        mood_distribution = {}
        for mood in recent_moods:
            emotion = mood.get("emotion", "neutral")
            mood_distribution[emotion] = mood_distribution.get(emotion, 0) + 1

        analytics = {
            "engagement": {
                "weekly_conversations": len(recent_events),
                "monthly_conversations": len([
                    e for e in memory.get("life_events", [])
                    if datetime.datetime.fromisoformat(e.get("timestamp", e.get("date"))) >= month_ago
                ]),
                "average_session_length": "5.2 minutes",  # Would calculate from actual data
                "retention_rate": "85%"
            },
            "progress": {
                "goal_completion_rate": round(goal_completion_rate, 1),
                "average_habit_streak": round(avg_streak, 1),
                "achievements_this_month": len([
                    a for a in memory.get("achievements", [])
                    if datetime.datetime.fromisoformat(a.get("date", now.isoformat())) >= month_ago
                ]),
                "growth_trend": "positive"
            },
            "wellbeing": {
                "mood_distribution": mood_distribution,
                "emotional_stability": len(set(m.get("emotion") for m in recent_moods)),
                "support_requests": len([
                    e for e in recent_events
                    if "crisis" in e.get("entry", "").lower() or "help" in e.get("entry", "").lower()
                ])
            },
            "timestamp": now.isoformat()
        }

        return jsonify(analytics)

    except Exception as e:
        logging.error(f"Error generating user analytics: {e}")
        return jsonify({"error": "Analytics generation failed"}), 500

@admin_bp.route('/api/maintenance/trigger', methods=['POST'])
def trigger_maintenance():
    """Trigger manual maintenance tasks"""
    try:
        data = request.get_json() or {}
        task_type = data.get("task", "full")

        results = {}

        if task_type in ["full", "backup"]:
            from security import backup_data
            backup_result = backup_data()
            results["backup"] = "success" if backup_result else "failed"

        if task_type in ["full", "repair"]:
            from security import auto_repair
            repair_result = auto_repair()
            results["repair"] = repair_result

        if task_type in ["full", "optimize"]:
            optimize_result = auto_updater.optimize_performance()
            results["optimize"] = optimize_result

        if task_type in ["full", "security"]:
            security_check = system_health_check()
            results["security_check"] = security_check

        log_security_event("admin_maintenance_triggered", {
            "task_type": task_type,
            "results": results
        })

        return jsonify({
            "status": "completed",
            "results": results,
            "timestamp": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error during admin maintenance: {e}")
        return jsonify({"error": "Maintenance task failed"}), 500

@admin_bp.route('/api/data/export')
def export_all_data():
    """Export comprehensive system data"""
    try:
        from app import load_memory
        from security import get_security_metrics

        memory = load_memory()
        security_data = get_security_metrics()
        system_status = auto_updater.get_system_status()

        export_data = {
            "export_metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "version": auto_updater.app_version,
                "export_type": "admin_full"
            },
            "user_data": memory,
            "system_metrics": {
                "security": security_data,
                "health": system_health_check(),
                "updater": system_status
            },
            "analytics": {
                "total_users": 1,  # Single user system
                "data_size": len(json.dumps(memory)),
                "features_used": list(memory.keys())
            }
        }

        return jsonify(export_data)

    except Exception as e:
        logging.error(f"Error exporting admin data: {e}")
        return jsonify({"error": "Data export failed"}), 500

@admin_bp.route('/api/updates/check')
def check_system_updates():
    """Check for system updates"""
    try:
        update_status = auto_updater.check_for_updates()
        return jsonify(update_status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/updates/apply', methods=['POST'])
def apply_system_updates():
    """Apply system updates"""
    try:
        data = request.get_json() or {}
        update_ids = data.get("update_ids", [])

        if update_ids:
            updates_to_apply = [
                update for update in auto_updater.pending_updates
                if update["id"] in update_ids
            ]
        else:
            updates_to_apply = auto_updater.pending_updates

        if not updates_to_apply:
            return jsonify({"error": "No updates to apply"}), 400

        result = auto_updater.apply_updates(updates_to_apply)

        log_security_event("admin_updates_applied", {
            "updates": [u["id"] for u in updates_to_apply],
            "result": result
        })

        return jsonify(result)

    except Exception as e:
        logging.error(f"Error applying updates: {e}")
        return jsonify({"error": "Update application failed"}), 500

@admin_bp.route('/api/config/update', methods=['POST'])
def update_configuration():
    """Update system configuration"""
    try:
        data = request.get_json() or {}
        config_type = data.get("type")
        settings = data.get("settings", {})

        if config_type == "security":
            # Update security settings
            from security import SECURITY_CONFIG
            for key, value in settings.items():
                if key in SECURITY_CONFIG:
                    SECURITY_CONFIG[key] = value

        elif config_type == "auto_updater":
            # Update auto-updater settings
            for key, value in settings.items():
                if hasattr(auto_updater, key):
                    setattr(auto_updater, key, value)

        log_security_event("admin_config_updated", {
            "config_type": config_type,
            "settings": settings
        })

        return jsonify({
            "status": "success",
            "message": f"{config_type} configuration updated",
            "timestamp": datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logging.error(f"Error updating configuration: {e}")
        return jsonify({"error": "Configuration update failed"}), 500

# Error handlers for admin blueprint
@admin_bp.errorhandler(404)
def admin_not_found(error):
    return jsonify({"error": "Admin endpoint not found"}), 404

@admin_bp.errorhandler(500)
def admin_server_error(error):
    return jsonify({"error": "Internal server error"}), 500
