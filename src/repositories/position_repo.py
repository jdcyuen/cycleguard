import psycopg
from core.logger import get_logger
from models.position import Position

logger = get_logger(__name__)

class PositionRepositoryError(Exception):
    """Raised when position repository operations fail."""

class PositionRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert( self, position: Position, ) -> None:

        """ 
        Insert a Position into the database. 
        """ 
        logger.info( "Inserting position " 
                    "security_id=%s " 
                    "snapshot_id=%s", 
                    position.security_id, 
                    position.snapshot_id, 
        ) 
        
        logger.debug( "Position: %s", position, )

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cycleguard.positions (
                        snapshot_id,
                        account_id,
                        security_id,
                        quantity,
                        avg_cost,
                        cost_basis_total,
                        current_value,
                        percent_of_account,
                        daily_gain,
                        daily_gain_pct,
                        total_gain,
                        total_gain_pct
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        position.snapshot_id, 
                        position.account_id, 
                        position.security_id, 
                        position.quantity, 
                        position.ave_cost, 
                        position.cost_basis_total, 
                        position.current_value, 
                        position.percent_of_account, 
                        position.daily_gain, 
                        position.daily_gain_pct, 
                        position.total_gain, 
                        position.total_gain_pct,
                    ),
                )

            self.conn.commit()
            logger.info(
                f"Position inserted successfully for security_id={position.security_id}"
            )

        except psycopg.IntegrityError as exc:
            self.conn.rollback()
            logger.exception( "Duplicate position." )
            raise PositionRepositoryError(
                f"Position already exists for "
                f"snapshot_id={position.snapshot_id}, "
                f"security_id={position.security_id}"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()
            logger.exception(
                f"Failed to insert position "
                f"for security_id={position.security_id}"
            )
            raise PositionRepositoryError(
                f"Failed to insert position "
                f"for security_id={position.security_id}"
            ) from exc

    def get_by_snapshot( self, snapshot_id: int, ) -> list[Position]: 
        
        """ 
        Returns all positions for a snapshot. 
        """ 
        
        logger.info( "Retrieving positions " "for snapshot_id=%s", snapshot_id, ) 
        
        try: 
            with self.conn.cursor() as cur: 
                cur.execute( 
                    """ 
                    SELECT id, account_id, security_id, snapshot_id, quantity, avg_cost, cost_basis_total, current_value, percent_of_account, daily_gain, daily_gain_pct, total_gain, total_gain_pct 
                    FROM cycleguard.positions 
                    WHERE snapshot_id = %s ORDER BY security_id """, (snapshot_id,), 
                ) 
                
                rows = cur.fetchall() 
                return [ 
                    Position( 
                        id=row[0], 
                        account_id=row[1], 
                        security_id=row[2], 
                        snapshot_id=row[3], 
                        quantity=row[4], 
                        ave_cost=row[5], 
                        cost_basis_total=row[6], 
                        current_value=row[7], 
                        percent_of_account=row[8], 
                        daily_gain=row[9], 
                        daily_gain_pct=row[10], 
                        total_gain=row[11], 
                        total_gain_pct=row[12], 
                    ) for row in rows ] 
        except psycopg.Error as exc: 
            logger.exception( "Failed retrieving positions." ) 
            raise PositionRepositoryError( "Failed retrieving positions." ) from exc  

    def delete_by_snapshot( self, snapshot_id: int, ) -> int: 
        """ 
        Deletes all positions for a snapshot. Returns: Number of rows deleted. 
        """ 
        logger.info( "Deleting positions " "for snapshot_id=%s", snapshot_id, )

        try: 
            with self.conn.cursor() as cur: 
                cur.execute( 
                    """ 
                    DELETE FROM cycleguard.positions 
                    WHERE snapshot_id = %s 
                    """, 
                    (snapshot_id,), 
                ) 
                rows_deleted = cur.rowcount 

            self.conn.commit() 
            
            logger.info( "Deleted %d positions.", rows_deleted, ) 
            return rows_deleted 

        except psycopg.Error as exc: 
            self.conn.rollback() 
            logger.exception( "Failed deleting positions." ) 
            raise PositionRepositoryError( "Failed deleting positions." ) from exc      