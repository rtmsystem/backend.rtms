"""
Script de prueba para el sistema de matches.
Este script prueba la funcionalidad de generación de brackets.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.organizations.models import Organization
from apps.players.models import PlayerProfile
from apps.geographical.models import Country
from apps.tournaments.models import (
    Tournament,
    TournamentDivision,
    Involvement,
    TournamentFormat,
    TournamentStatus,
    GenderType,
    ParticipantType,
    InvolvementStatus,
)
from apps.matches.models import Match
from apps.matches.services import MatchBracketGenerationService
from apps.matches.exceptions import MatchBusinessError

User = get_user_model()


def create_test_data():
    """Crear datos de prueba para testing."""
    print("=" * 60)
    print("CREANDO DATOS DE PRUEBA")
    print("=" * 60)
    
    # Crear usuario admin
    admin_user, created = User.objects.get_or_create(
        email='admin@test.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Test',
            'role': 'admin',
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
        print(f"✅ Usuario admin creado: {admin_user.email}")
    else:
        print(f"ℹ️  Usuario admin ya existe: {admin_user.email}")
    
    # Crear organización
    organization, created = Organization.objects.get_or_create(
        nit='123456789',
        defaults={
            'name': 'Test Organization',
            'created_by': admin_user,
        }
    )
    if created:
        print(f"✅ Organización creada: {organization.name}")
    else:
        print(f"ℹ️  Organización ya existe: {organization.name}")
    
    # Crear torneo
    start_date = timezone.now() + timedelta(days=30)
    end_date = timezone.now() + timedelta(days=33)
    registration_deadline = timezone.now() + timedelta(days=25)
    
    tournament, created = Tournament.objects.get_or_create(
        name='Test Tournament',
        defaults={
            'description': 'Tournament for testing matches',
            'organization': organization,
            'contact_name': 'Test Contact',
            'contact_phone': '1234567890',
            'contact_email': 'contact@test.com',
            'start_date': start_date,
            'end_date': end_date,
            'registration_deadline': registration_deadline,
            'city': 'Lima',
            'country': 'Peru',
            'status': TournamentStatus.PUBLISHED,
            'created_by': admin_user,
        }
    )
    if created:
        print(f"✅ Torneo creado: {tournament.name}")
    else:
        print(f"ℹ️  Torneo ya existe: {tournament.name}")
    
    # Crear división Single Elimination
    division_knockout, created = TournamentDivision.objects.get_or_create(
        tournament=tournament,
        name='Men Singles - Knockout',
        defaults={
            'description': 'Men singles division with knockout format',
            'format': TournamentFormat.KNOCKOUT,
            'max_participants': 16,
            'gender': GenderType.MALE,
            'participant_type': ParticipantType.SINGLE,
            'is_active': True,
            'is_published': True,
        }
    )
    if created:
        division_knockout.published_by = admin_user
        division_knockout.save()
        print(f"✅ División creada: {division_knockout.name}")
    else:
        print(f"ℹ️  División ya existe: {division_knockout.name}")
    
    # Crear división Double Elimination
    division_double, created = TournamentDivision.objects.get_or_create(
        tournament=tournament,
        name='Men Singles - Double Elimination',
        defaults={
            'description': 'Men singles division with double elimination format',
            'format': TournamentFormat.DOUBLE_SLASH,
            'max_participants': 8,
            'gender': GenderType.MALE,
            'participant_type': ParticipantType.SINGLE,
            'is_active': True,
            'is_published': True,
        }
    )
    if created:
        division_double.published_by = admin_user
        division_double.save()
        print(f"✅ División creada: {division_double.name}")
    else:
        print(f"ℹ️  División ya existe: {division_double.name}")
    
    # Crear o obtener país para los perfiles
    country, _ = Country.objects.get_or_create(
        name='Peru',
        defaults={
            'phone_code': '+51',
            'flag': '🇵🇪',
        }
    )
    
    # Crear jugadores y sus perfiles
    players = []
    for i in range(1, 9):  # 8 jugadores
        user, created = User.objects.get_or_create(
            email=f'player{i}@test.com',
            defaults={
                'first_name': f'Player',
                'last_name': f'{i}',
                'role': 'player',
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        profile, created = PlayerProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'gender': 'male',
                'nationality': country,
                'date_of_birth': '2000-01-01',
            }
        )
        players.append(profile)
    
    print(f"✅ {len(players)} jugadores creados/preparados")
    
    # Despublicar temporalmente las divisiones para poder crear involvements
    was_knockout_published = division_knockout.is_published
    was_double_published = division_double.is_published
    
    if was_knockout_published:
        division_knockout.is_published = False
        division_knockout.save(update_fields=['is_published'])
    
    if was_double_published:
        division_double.is_published = False
        division_double.save(update_fields=['is_published'])
    
    # Crear involvements aprobados para división Knockout (8 jugadores)
    involvements_knockout = []
    for i, player in enumerate(players[:8]):
        involvement, created = Involvement.objects.get_or_create(
            tournament=tournament,
            division=division_knockout,
            player=player,
            defaults={
                'status': InvolvementStatus.APPROVED,
                'paid': True,
            }
        )
        if created:
            involvements_knockout.append(involvement)
        elif involvement.status == InvolvementStatus.APPROVED:
            involvements_knockout.append(involvement)
        else:
            involvement.status = InvolvementStatus.APPROVED
            involvement.paid = True
            involvement.save()
            involvements_knockout.append(involvement)
    
    print(f"✅ {len(involvements_knockout)} involvements aprobados para división Knockout")
    
    # Crear involvements aprobados para división Double Elimination (4 jugadores)
    involvements_double = []
    for i, player in enumerate(players[:4]):
        involvement, created = Involvement.objects.get_or_create(
            tournament=tournament,
            division=division_double,
            player=player,
            defaults={
                'status': InvolvementStatus.APPROVED,
                'paid': True,
            }
        )
        if created:
            involvements_double.append(involvement)
        elif involvement.status == InvolvementStatus.APPROVED:
            involvements_double.append(involvement)
        else:
            involvement.status = InvolvementStatus.APPROVED
            involvement.paid = True
            involvement.save()
            involvements_double.append(involvement)
    
    print(f"✅ {len(involvements_double)} involvements aprobados para división Double Elimination")
    
    # Volver a publicar las divisiones si estaban publicadas
    if was_knockout_published:
        division_knockout.is_published = True
        division_knockout.save(update_fields=['is_published'])
    
    if was_double_published:
        division_double.is_published = True
        division_double.save(update_fields=['is_published'])
    
    return {
        'admin_user': admin_user,
        'organization': organization,
        'tournament': tournament,
        'division_knockout': division_knockout,
        'division_double': division_double,
        'players': players,
        'involvements_knockout': involvements_knockout,
        'involvements_double': involvements_double,
    }


def test_bracket_generation_single_elimination(division, admin_user):
    """Probar generación de bracket para Single Elimination."""
    print("\n" + "=" * 60)
    print("PRUEBA 1: GENERACIÓN DE BRACKET - SINGLE ELIMINATION")
    print("=" * 60)
    
    # Limpiar partidos existentes
    Match.objects.filter(division=division).delete()
    print(f"🧹 Partidos existentes eliminados para la división: {division.name}")
    
    try:
        # Generar bracket
        service = MatchBracketGenerationService(
            division=division,
            user=admin_user,
        )
        matches = service.execute()
        
        print(f"\n✅ Bracket generado exitosamente!")
        print(f"📊 Total de partidos creados: {len(matches)}")
        
        # Mostrar información de partidos
        print("\n📋 Partidos creados:")
        print("-" * 60)
        matches_sorted = sorted(matches, key=lambda m: (m.round_number, m.match_code))
        for match in matches_sorted:
            bracket_type = "Losers" if match.is_losers_bracket else "Winners"
            player1 = f"{match.player1.first_name} {match.player1.last_name}" if match.player1 else "BYE"
            player2 = f"{match.player2.first_name} {match.player2.last_name}" if match.player2 else "BYE"
            next_match = f" -> {match.next_match.match_code}" if match.next_match else " -> FINAL"
            
            print(f"  {match.match_code:6} | Ronda {match.round_number} | {bracket_type:7} | "
                  f"{player1:20} vs {player2:20} {next_match}")
        
        # Verificar estructura
        print("\n🔍 Verificaciones:")
        
        # Contar partidos por ronda
        rounds = {}
        for match in matches:
            round_key = f"Ronda {match.round_number}"
            rounds[round_key] = rounds.get(round_key, 0) + 1
        
        print(f"  ✓ Partidos por ronda: {dict(rounds)}")
        
        # Verificar que no hay partidos de Losers bracket
        losers_matches = [m for m in matches if m.is_losers_bracket]
        if len(losers_matches) == 0:
            print("  ✓ No hay partidos en Losers bracket (correcto para Single Elimination)")
        else:
            print(f"  ⚠️  Advertencia: Se encontraron {len(losers_matches)} partidos en Losers bracket")
        
        # Verificar códigos únicos
        codes = [m.match_code for m in matches]
        if len(codes) == len(set(codes)):
            print("  ✓ Todos los códigos de partido son únicos")
        else:
            print(f"  ⚠️  Advertencia: Se encontraron códigos duplicados")
        
        return True
        
    except MatchBusinessError as e:
        print(f"\n❌ Error de negocio: {e.message}")
        print(f"   Código de error: {e.error_code}")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_bracket_generation_double_elimination(division, admin_user):
    """Probar generación de bracket para Double Elimination."""
    print("\n" + "=" * 60)
    print("PRUEBA 2: GENERACIÓN DE BRACKET - DOUBLE ELIMINATION")
    print("=" * 60)
    
    # Limpiar partidos existentes
    Match.objects.filter(division=division).delete()
    print(f"🧹 Partidos existentes eliminados para la división: {division.name}")
    
    try:
        # Generar bracket
        service = MatchBracketGenerationService(
            division=division,
            user=admin_user,
        )
        matches = service.execute()
        
        print(f"\n✅ Bracket generado exitosamente!")
        print(f"📊 Total de partidos creados: {len(matches)}")
        
        # Mostrar información de partidos
        print("\n📋 Partidos creados:")
        print("-" * 60)
        matches_sorted = sorted(matches, key=lambda m: (m.round_number if m.round_number != 999 else 9999, not m.is_losers_bracket, m.match_code))
        for match in matches_sorted:
            if match.round_number == 999:
                bracket_type = "Grand Final"
            else:
                bracket_type = "Losers" if match.is_losers_bracket else "Winners"
            player1 = f"{match.player1.first_name} {match.player1.last_name}" if match.player1 else "BYE"
            player2 = f"{match.player2.first_name} {match.player2.last_name}" if match.player2 else "BYE"
            next_match = f" -> {match.next_match.match_code}" if match.next_match else " -> FINAL"
            
            round_display = "Grand Final" if match.round_number == 999 else f"Ronda {match.round_number}"
            print(f"  {match.match_code:6} | {round_display:12} | {bracket_type:11} | "
                  f"{player1:20} vs {player2:20} {next_match}")
        
        # Verificar estructura
        print("\n🔍 Verificaciones:")
        
        # Contar partidos por tipo de bracket (excluir Grand Final)
        winners_matches = [m for m in matches if not m.is_losers_bracket and m.round_number != 999]
        losers_matches = [m for m in matches if m.is_losers_bracket]
        grand_final_matches = [m for m in matches if m.round_number == 999]
        
        print(f"  ✓ Partidos en Winners bracket: {len(winners_matches)}")
        print(f"  ✓ Partidos en Losers bracket: {len(losers_matches)}")
        if grand_final_matches:
            print(f"  ✓ Grand Final: {[m.match_code for m in grand_final_matches]}")
        
        # Verificar que hay partidos en ambos brackets
        if len(winners_matches) > 0 and len(losers_matches) > 0:
            print("  ✓ Se crearon partidos en ambos brackets (correcto para Double Elimination)")
        else:
            print("  ⚠️  Advertencia: No se crearon partidos en ambos brackets")
        
        # Verificar códigos únicos
        codes = [m.match_code for m in matches]
        if len(codes) == len(set(codes)):
            print("  ✓ Todos los códigos de partido son únicos")
        else:
            print(f"  ⚠️  Advertencia: Se encontraron códigos duplicados")
        
        # Verificar que hay Grand Final
        grand_finals = [m for m in matches if m.round_number == 999]
        if len(grand_finals) > 0:
            print(f"  ✓ Se creó la Grand Final: {[m.match_code for m in grand_finals]}")
        else:
            print("  ⚠️  Advertencia: No se encontró la Grand Final")
        
        return True
        
    except MatchBusinessError as e:
        print(f"\n❌ Error de negocio: {e.message}")
        print(f"   Código de error: {e.error_code}")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal."""
    print("\n" + "=" * 60)
    print("SCRIPT DE PRUEBA: SISTEMA DE MATCHES")
    print("=" * 60)
    
    # Crear datos de prueba
    test_data = create_test_data()
    
    # Ejecutar pruebas
    results = []
    
    # Prueba 1: Single Elimination
    result1 = test_bracket_generation_single_elimination(
        test_data['division_knockout'],
        test_data['admin_user']
    )
    results.append(('Single Elimination', result1))
    
    # Prueba 2: Double Elimination
    result2 = test_bracket_generation_double_elimination(
        test_data['division_double'],
        test_data['admin_user']
    )
    results.append(('Double Elimination', result2))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:30} : {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print(f"\n⚠️  {total - passed} prueba(s) fallaron")


if __name__ == '__main__':
    main()

