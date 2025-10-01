import oracledb

def get_connection():
    try:
        return oracledb.connect(
            user="rm562269",
            password="fiap25",
            host="oracle.fiap.com.br",
            port=1521,
            service_name="orcl",
        )
    except Exception as e:
        print(f"Erro ao obter a conexão: {e}")
        return None

def criar_e_atualizar_tabela():
    ddl = [
        """
        CREATE TABLE pacientes(
          id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          nome VARCHAR2(80) NOT NULL,
          cpf  VARCHAR2(20),
          nasc DATE,
          endereco VARCHAR2(120),
          telefone VARCHAR2(30)
        )
        """,
        """
        CREATE TABLE consultas(
          id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          paciente_id NUMBER NOT NULL,
          data_consulta DATE,
          hora VARCHAR2(5),
          especialidade VARCHAR2(60),
          obs VARCHAR2(200),
          CONSTRAINT fk_consulta_paciente
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
        """,
        "CREATE INDEX idx_consulta_pac_data_hora ON consultas(paciente_id, data_consulta, hora)",
    ]
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        for stmt in ddl:
            try:
                cur.execute(stmt)
            except oracledb.Error:
                conn.rollback()  # já existe -> ignora
        conn.commit()
        print("Esquema verificado/criado com sucesso.")
    except oracledb.Error as e:
        print(f"Erro de DDL: {e}")
        conn.rollback()
    finally:
        conn.close()

def criar_paciente():
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        nome = input("Nome completo: ")
        cpf = input("CPF (qualquer formato): ")
        nasc = input("Nascimento (dd/mm/aaaa ou deixe vazio): ")
        end = input("Endereço: ")
        tel = input("Telefone/WhatsApp: ")

        if nasc != "":
            cur.execute(
                """
                INSERT INTO pacientes (nome, cpf, nasc, endereco, telefone)
                VALUES (:n, :c, TO_DATE(:d,'DD/MM/YYYY'), :e, :t)
                """,
                {"n": nome, "c": cpf, "d": nasc, "e": end, "t": tel},
            )
        else:
            cur.execute(
                """
                INSERT INTO pacientes (nome, cpf, nasc, endereco, telefone)
                VALUES (:n, :c, NULL, :e, :t)
                """,
                {"n": nome, "c": cpf, "e": end, "t": tel},
            )
        conn.commit()
        print("Paciente cadastrado.")
    except oracledb.Error as e:
        print(f"Erro ao cadastrar paciente: {e}")
        conn.rollback()
    finally:
        conn.close()

def listar_pacientes(busca=None):
    """Lista pacientes sempre por nome (sem ordenar por nascimento)."""
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        if busca is not None and busca != "":
            cur.execute(
                """
                SELECT id, nome, cpf,
                       NVL(TO_CHAR(nasc,'DD/MM/YYYY'),''),
                       NVL(endereco,''), NVL(telefone,'')
                  FROM pacientes
                 WHERE LOWER(nome) LIKE :b OR cpf LIKE :b
                 ORDER BY nome
                """,
                {"b": f"%{str(busca).lower()}%"},
            )
        else:
            cur.execute(
                """
                SELECT id, nome, cpf,
                       NVL(TO_CHAR(nasc,'DD/MM/YYYY'),''),
                       NVL(endereco,''), NVL(telefone,'')
                  FROM pacientes
                 ORDER BY nome
                """
            )
        rows = cur.fetchall()
        if not rows:
            print("Nenhum paciente cadastrado.")
            return
        print("\n-- Pacientes --")
        for r in rows:
            print(f"{r[0]:>3} | {r[1]} | CPF:{r[2]} | Nasc:{r[3]} | Tel:{r[5]}")
    except oracledb.Error as e:
        print(f"Erro ao listar pacientes: {e}")
    finally:
        conn.close()

def atualizar_paciente():
    listar_pacientes()
    pid = input("ID do paciente a atualizar: ")
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, cpf, TO_CHAR(nasc,'DD/MM/YYYY'), endereco, telefone FROM pacientes WHERE id = :id",
            {"id": pid},
        )
        row = cur.fetchone()
        if not row:
            print("Paciente não encontrado.")
            return

        nome = input(f"Nome [{row[1]}]: ")
        if nome == "":
            nome = row[1]
        cpf  = input(f"CPF [{row[2]}]: ")
        if cpf == "":
            cpf = row[2]
        nasc = input(f"Nascimento [{row[3] or ''}] (dd/mm/aaaa ou vazio p/ NULL): ")
        end  = input(f"Endereço [{row[4] or ''}]: ")
        if end == "":
            end = row[4]
        tel  = input(f"Telefone [{row[5] or ''}]: ")
        if tel == "":
            tel = row[5]

        if nasc != "":
            cur.execute(
                """
                UPDATE pacientes
                   SET nome=:n, cpf=:c, nasc=TO_DATE(:d,'DD/MM/YYYY'),
                       endereco=:e, telefone=:t
                 WHERE id=:id
                """,
                {"n": nome, "c": cpf, "d": nasc, "e": end, "t": tel, "id": pid},
            )
        else:
            cur.execute(
                """
                UPDATE pacientes
                   SET nome=:n, cpf=:c, nasc=NULL,
                       endereco=:e, telefone=:t
                 WHERE id=:id
                """,
                {"n": nome, "c": cpf, "e": end, "t": tel, "id": pid},
            )
        conn.commit()
        print("Paciente atualizado.")
    except oracledb.Error as e:
        print(f"Erro ao atualizar paciente: {e}")
        conn.rollback()
    finally:
        conn.close()

def excluir_paciente():
    listar_pacientes()
    pid = input("ID do paciente a excluir: ")
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM pacientes WHERE id = :id", {"id": pid})
        conn.commit()
        print("Paciente excluído." if cur.rowcount else "Paciente não encontrado.")
    except oracledb.Error as e:
        print(f"Erro ao excluir paciente: {e}")
        conn.rollback()
    finally:
        conn.close()

def criar_consulta():
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        listar_pacientes()
        pid = input("ID do paciente: ")
        data_c = input("Data da consulta (dd/mm/aaaa ou vazio p/ NULL): ")
        hora   = input("Hora (hh:mm, opcional): ")
        esp    = input("Especialidade (opcional): ")
        obs    = input("Observações (opcional): ")

        if data_c != "":
            cur.execute(
                """
                INSERT INTO consultas (paciente_id, data_consulta, hora, especialidade, obs)
                VALUES (:p, TO_DATE(:d,'DD/MM/YYYY'), :h, :e, :o)
                """,
                {"p": pid, "d": data_c, "h": hora, "e": esp, "o": obs},
            )
        else:
            cur.execute(
                """
                INSERT INTO consultas (paciente_id, data_consulta, hora, especialidade, obs)
                VALUES (:p, NULL, :h, :e, :o)
                """,
                {"p": pid, "h": hora, "e": esp, "o": obs},
            )
        conn.commit()
        print("Consulta agendada.")
    except oracledb.Error as e:
        print(f"Erro ao agendar consulta: {e}")
        conn.rollback()
    finally:
        conn.close()

def listar_consultas(filtro_paciente=None):
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        if filtro_paciente is not None and filtro_paciente != "":
            cur.execute(
                """
                SELECT c.id, NVL(TO_CHAR(c.data_consulta,'DD/MM/YYYY'),''), NVL(c.hora,''), 
                       NVL(c.especialidade,''), NVL(c.obs,''), p.nome
                  FROM consultas c
                  JOIN pacientes p ON p.id = c.paciente_id
                 WHERE p.id = :pid
                 ORDER BY c.data_consulta, c.hora
                """,
                {"pid": filtro_paciente},
            )
        else:
            cur.execute(
                """
                SELECT c.id, NVL(TO_CHAR(c.data_consulta,'DD/MM/YYYY'),''), NVL(c.hora,''), 
                       NVL(c.especialidade,''), NVL(c.obs,''), p.nome
                  FROM consultas c
                  JOIN pacientes p ON p.id = c.paciente_id
                 ORDER BY c.data_consulta, c.hora
                """
            )
        rows = cur.fetchall()
        if not rows:
            print("Nenhuma consulta encontrada.")
            return
        print("\n-- Consultas --")
        for r in rows:
            print(f"{r[0]:>3} | {r[1]} {r[2]} | {r[3]:<18} | Paciente: {r[5]} | Obs: {r[4]}")
    except oracledb.Error as e:
        print(f"Erro ao listar consultas: {e}")
    finally:
        conn.close()

def atualizar_consulta():
    listar_consultas()
    cid = input("ID da consulta a atualizar: ")
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, paciente_id, NVL(TO_CHAR(data_consulta,'DD/MM/YYYY'),''), hora,
                   NVL(especialidade,''), NVL(obs,'')
              FROM consultas WHERE id = :id
            """,
            {"id": cid},
        )
        row = cur.fetchone()
        if not row:
            print("Consulta não encontrada.")
            return

        listar_pacientes()
        pid = input(f"Paciente ID [{row[1]}]: ")
        if pid == "":
            pid = row[1]
        data_c = input(f"Data [{row[2]}] (dd/mm/aaaa ou vazio p/ NULL): ")
        hora   = input(f"Hora [{row[3]}]: ")
        if hora == "":
            hora = row[3]
        esp    = input(f"Especialidade [{row[4]}]: ")
        if esp == "":
            esp = row[4]
        obs    = input(f"Obs [{row[5]}]: ")
        if obs == "":
            obs = row[5]

        if data_c != "":
            cur.execute(
                """
                UPDATE consultas
                   SET paciente_id=:p, data_consulta=TO_DATE(:d,'DD/MM/YYYY'),
                       hora=:h, especialidade=:e, obs=:o
                 WHERE id=:id
                """,
                {"p": pid, "d": data_c, "h": hora, "e": esp, "o": obs, "id": cid},
            )
        else:
            cur.execute(
                """
                UPDATE consultas
                   SET paciente_id=:p, data_consulta=NULL,
                       hora=:h, especialidade=:e, obs=:o
                 WHERE id=:id
                """,
                {"p": pid, "h": hora, "e": esp, "o": obs, "id": cid},
            )
        conn.commit()
        print("Consulta atualizada.")
    except oracledb.Error as e:
        print(f"Erro ao atualizar consulta: {e}")
        conn.rollback()
    finally:
        conn.close()

def excluir_consulta():
    listar_consultas()
    cid = input("ID da consulta a excluir: ")
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM consultas WHERE id = :id", {"id": cid})
        conn.commit()
        print("Consulta excluída." if cur.rowcount else "Consulta não encontrada.")
    except oracledb.Error as e:
        print(f"Erro ao excluir consulta: {e}")
        conn.rollback()
    finally:
        conn.close()

def menu_pacientes():
    while True:
        print("""
-- Pacientes --
1. Cadastrar
2. Listar (por nome)
3. Buscar por nome/CPF
4. Atualizar
5. Excluir
0. Voltar
""")
        op = input("Opção: ")
        if op == "1":
            criar_paciente()
        elif op == "2":
            listar_pacientes()
        elif op == "3":
            termo = input("Buscar: ")
            listar_pacientes(termo)
        elif op == "4":
            atualizar_paciente()
        elif op == "5":
            excluir_paciente()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

def menu_consultas():
    while True:
        print("""
-- Consultas --
1. Agendar
2. Listar todas
3. Listar por paciente
4. Atualizar
5. Excluir
0. Voltar
""")
        op = input("Opção: ")
        if op == "1":
            criar_consulta()
        elif op == "2":
            listar_consultas()
        elif op == "3":
            pid = input("ID do paciente: ")
            listar_consultas(pid)
        elif op == "4":
            atualizar_consulta()
        elif op == "5":
            excluir_consulta()
        elif op == "0":
            break
        else:
            print("Opção inválida.")

def main():
    print("==============================")
    print("=========== HC APP ===========")
    print("==============================")
    while True:
        print("""
Menu Principal
1. Pacientes
2. Consultas
9. Criar/Atualizar tabela 
0. Sair
""")
        op = input("Opção: ")
        try:
            if op == "1":
                menu_pacientes()
            elif op == "2":
                menu_consultas()
            elif op == "9":
                criar_e_atualizar_tabela()
            elif op == "0":
                print("Saindo...")
                break
            else:
                print("Opção inválida.")
        except KeyboardInterrupt:
            print("\nOperação cancelada.")
        except Exception as e:
            print(f"[ERRO] inesperado: {e}")
        finally:
            pass

if __name__ == "__main__":
    main()
