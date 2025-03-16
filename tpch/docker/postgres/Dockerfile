FROM postgres:latest

ENV POSTGRES_PASSWORD=Dlghdms0228

USER root
RUN apt-get update && apt-get install -y git make gcc
RUN git clone https://github.com/electrum/tpch-dbgen.git /opt/tpch-dbgen

WORKDIR /opt/tpch-dbgen
RUN make
RUN ./dbgen -s 1

RUN for file in *.tbl; do \
    tmpfile="$(mktemp)"; \
    sed 's/|$//' "$file" > "$tmpfile" && mv "$tmpfile" "$file"; \
done

RUN chown -R postgres:postgres /opt/tpch-dbgen

USER postgres

RUN initdb -D /var/lib/postgresql/data

RUN echo "host    all             all             172.20.0.0/16            trust" >> /var/lib/postgresql/data/pg_hba.conf

RUN pg_ctl -D /var/lib/postgresql/data -o "-c listen_addresses='localhost'" -w start \
    && psql -U postgres -c "CREATE DATABASE tpch;" \
    && psql -U postgres -d tpch -f /opt/tpch-dbgen/dss.ddl \
    \
    && psql -U postgres -d tpch -c "\COPY region   FROM '/opt/tpch-dbgen/region.tbl'   DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY nation   FROM '/opt/tpch-dbgen/nation.tbl'   DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY part     FROM '/opt/tpch-dbgen/part.tbl'     DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY supplier FROM '/opt/tpch-dbgen/supplier.tbl' DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY partsupp FROM '/opt/tpch-dbgen/partsupp.tbl' DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY customer FROM '/opt/tpch-dbgen/customer.tbl' DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY orders   FROM '/opt/tpch-dbgen/orders.tbl'   DELIMITER '|' CSV;" \
    && psql -U postgres -d tpch -c "\COPY lineitem FROM '/opt/tpch-dbgen/lineitem.tbl' DELIMITER '|' CSV;" \
    \
    && psql -U postgres -d tpch -c "ALTER TABLE nation    ADD CONSTRAINT pk_nation    PRIMARY KEY (n_nationkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE region    ADD CONSTRAINT pk_region    PRIMARY KEY (r_regionkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE part      ADD CONSTRAINT pk_part      PRIMARY KEY (p_partkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE supplier  ADD CONSTRAINT pk_supplier  PRIMARY KEY (s_suppkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE partsupp  ADD CONSTRAINT pk_partsupp  PRIMARY KEY (ps_partkey, ps_suppkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE customer  ADD CONSTRAINT pk_customer  PRIMARY KEY (c_custkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE orders    ADD CONSTRAINT pk_orders    PRIMARY KEY (o_orderkey);" \
    && psql -U postgres -d tpch -c "ALTER TABLE lineitem  ADD CONSTRAINT pk_lineitem  PRIMARY KEY (l_orderkey, l_linenumber);" \
    \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_customer_nationkey ON customer (c_nationkey);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_orders_custkey      ON orders   (o_custkey);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_orders_orderdate    ON orders   (o_orderdate);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_lineitem_partkey    ON lineitem (l_partkey);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_lineitem_suppkey    ON lineitem (l_suppkey);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_lineitem_shipdate   ON lineitem (l_shipdate);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_partsupp_suppkey    ON partsupp (ps_suppkey);" \
    && psql -U postgres -d tpch -c "CREATE INDEX idx_supplier_nationkey  ON supplier (s_nationkey);" \
    \
    && pg_ctl -D /var/lib/postgresql/data -m fast -w stop

USER root
RUN rm -rf /opt/tpch-dbgen

EXPOSE 5432
CMD ["postgres"]