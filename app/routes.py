from __future__ import annotations

from http import HTTPStatus
from typing import Any, List

from flask import Blueprint, Flask, jsonify, render_template, request

from .blob_client import BlobClient
from .db import close_db_session, get_db_session
from .repository import NoteRepository


def register_routes(app: Flask) -> None:
    """
    注册首页与 API 路由，并挂载数据库 session 生命周期钩子。
    """
    main_bp = Blueprint("main", __name__)
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @main_bp.route("/", methods=["GET"])
    def index() -> Any:
        return render_template("index.html")

    @api_bp.route("/notes", methods=["GET"])
    def list_notes() -> Any:
        session = get_db_session()
        repo = NoteRepository(session)
        notes = [n.to_dict() for n in repo.list_notes()]
        return jsonify(notes)

    def _validate_files(max_files: int = 3, max_size_mb: int = 5) -> List[str]:
        """
        校验上传文件数量与大小，返回文件名列表。
        """
        files = request.files.getlist("images")
        if len(files) > max_files:
            raise ValueError("最多 3 张图片")
        max_bytes = max_size_mb * 1024 * 1024
        filenames: List[str] = []
        for f in files:
            f.seek(0, 2)
            size = f.tell()
            f.seek(0)
            if size > max_bytes:
                raise ValueError("单张图片不能超过 5MB")
            filenames.append(f.filename or "image")
        return filenames

    def _handle_upload() -> List[str]:
        """
        上传请求中的 files，返回新增的 blob URL 列表。
        """
        files = request.files.getlist("images")
        if not files:
            return []
        client = BlobClient()
        payload = []
        for f in files:
            payload.append((f.filename or "image", f.read()))
        return client.upload_files(payload)

    @api_bp.route("/notes", methods=["POST"])
    def create_note() -> Any:
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        color = request.form.get("color", "#FFE57F").strip()

        try:
            _validate_files()
        except ValueError as e:
            return jsonify({"error": str(e)}), HTTPStatus.BAD_REQUEST

        if not title or len(title) > 30:
            return jsonify({"error": "Invalid title"}), HTTPStatus.BAD_REQUEST
        if not content or len(content) > 500:
            return jsonify({"error": "Invalid content"}), HTTPStatus.BAD_REQUEST

        new_urls = _handle_upload()

        session = get_db_session()
        repo = NoteRepository(session)
        note = repo.create(
            title=title,
            content=content,
            color=color,
            image_urls=new_urls,
        )
        return jsonify(note.to_dict()), HTTPStatus.CREATED

    @api_bp.route("/notes/<int:note_id>", methods=["PUT"])
    def update_note(note_id: int) -> Any:
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        color = request.form.get("color", "#FFE57F").strip()
        # 前端传递已有图片 URL
        existing_urls = request.form.getlist("existing_urls")
        # 前端传递需要删除的 URL
        deleted_urls = request.form.getlist("deleted_urls")

        try:
            _validate_files()
        except ValueError as e:
            return jsonify({"error": str(e)}), HTTPStatus.BAD_REQUEST

        if not title or len(title) > 30:
            return jsonify({"error": "Invalid title"}), HTTPStatus.BAD_REQUEST
        if not content or len(content) > 500:
            return jsonify({"error": "Invalid content"}), HTTPStatus.BAD_REQUEST

        session = get_db_session()
        repo = NoteRepository(session)
        note = repo.get(note_id)
        if note is None:
            return jsonify({"error": "Note not found"}), HTTPStatus.NOT_FOUND

        new_urls = _handle_upload()
        final_urls = [u for u in existing_urls if u not in deleted_urls] + new_urls

        # 删除已选的旧图片
        if deleted_urls:
            try:
                client = BlobClient()
                client.delete_urls(deleted_urls)
            except RuntimeError:
                # 不中断主流程，记录即可
                pass

        note = repo.update(
            note,
            title=title,
            content=content,
            color=color,
            image_urls=final_urls,
        )
        return jsonify(note.to_dict())

    @api_bp.route("/notes/<int:note_id>", methods=["DELETE"])
    def delete_note(note_id: int) -> Any:
        session = get_db_session()
        repo = NoteRepository(session)
        note = repo.get(note_id)
        if note is None:
            return jsonify({"error": "Note not found"}), HTTPStatus.NOT_FOUND

        # 删除 Blob 文件
        if note.image_urls:
            try:
                client = BlobClient()
                client.delete_urls(note.image_urls)
            except RuntimeError:
                pass

        repo.delete(note)
        return jsonify({"success": True})

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # 请求结束时关闭数据库 session
    app.teardown_appcontext(close_db_session)


