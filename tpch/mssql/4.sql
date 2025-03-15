select
	o_orderpriority,
	count(*) as order_count
from
	orders
where
	o_orderdate >= '1994/12/01'
	and o_orderdate < dateadd(mm,3, '1994/12/01')
	and exists (
		select
			*
		from
			lineitem
		where
			l_orderkey = o_orderkey
			and l_commitdate < l_receiptdate
	)
group by
	o_orderpriority
order by
	o_orderpriority;

 
