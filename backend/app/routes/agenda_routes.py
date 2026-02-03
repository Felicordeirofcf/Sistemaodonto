from flask import Blueprint, jsonify, request
from app.models import db, Appointment, Patient, User, Lead
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

agenda_bp = Blueprint('agenda_bp', __name__)

def _get_clinic_id():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity.get("clinic_id")
    user = User.query.get(identity)
    return user.clinic_id if user else None

@agenda_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    clinic_id = _get_clinic_id()
    start_str = request.args.get('from')
    end_str = request.args.get('to')
    
    query = Appointment.query.filter_by(clinic_id=clinic_id)
    
    if start_str:
        try:
            start_dt = datetime.fromisoformat(start_str)
            query = query.filter(Appointment.start_datetime >= start_dt)
        except: pass
    if end_str:
        try:
            end_dt = datetime.fromisoformat(end_str)
            query = query.filter(Appointment.start_datetime <= end_dt)
        except: pass
        
    appointments = query.order_by(Appointment.start_datetime).all()
    return jsonify([appt.to_dict() for appt in appointments]), 200

@agenda_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    clinic_id = _get_clinic_id()
    data = request.get_json()
    
    try:
        start_dt = datetime.fromisoformat(data['start'])
        # Default duration 1 hour if end not provided
        if 'end' in data:
            end_dt = datetime.fromisoformat(data['end'])
        else:
            end_dt = start_dt + timedelta(hours=float(data.get('duration', 1)))
            
        new_appt = Appointment(
            clinic_id=clinic_id,
            patient_id=data.get('patient_id'),
            lead_id=data.get('lead_id'),
            title=data.get('title') or data.get('patient_name'),
            description=data.get('description') or data.get('procedure'),
            start_datetime=start_dt,
            end_datetime=end_dt,
            status=data.get('status', 'scheduled')
        )
        
        db.session.add(new_appt)
        db.session.commit()
        return jsonify(new_appt.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@agenda_bp.route('/appointments/<int:id>', methods=['PATCH'])
@jwt_required()
def update_appointment(id):
    clinic_id = _get_clinic_id()
    appt = Appointment.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    data = request.get_json()
    
    try:
        if 'start' in data:
            appt.start_datetime = datetime.fromisoformat(data['start'])
        if 'end' in data:
            appt.end_datetime = datetime.fromisoformat(data['end'])
        if 'title' in data:
            appt.title = data['title']
        if 'description' in data:
            appt.description = data['description']
        if 'status' in data:
            appt.status = data['status']
        if 'patient_id' in data:
            appt.patient_id = data['patient_id']
            
        db.session.commit()
        return jsonify(appt.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@agenda_bp.route('/appointments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(id):
    clinic_id = _get_clinic_id()
    appt = Appointment.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    
    db.session.delete(appt)
    db.session.commit()
    return jsonify({"message": "Agendamento removido"}), 200
