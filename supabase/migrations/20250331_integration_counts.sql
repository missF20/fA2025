-- Create a function to get integration counts by type

CREATE OR REPLACE FUNCTION get_integration_counts("table_name" text)
RETURNS TABLE (integration_type text, count bigint)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY EXECUTE 'SELECT integration_type::text, COUNT(*)::bigint as count 
         FROM ' || quote_ident(table_name) || ' 
         GROUP BY integration_type';
END;
$$;