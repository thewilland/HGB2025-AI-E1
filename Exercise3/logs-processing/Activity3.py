from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, lower, count, desc, window, to_timestamp, expr
from pyspark.sql.types import StructType, StructField, StringType, LongType

# 1. Configuration & Session Setup
CHECKPOINT_PATH = "/tmp/spark-checkpoints/logs-processing"

spark = (
    SparkSession.builder
    .appName("LogsProcessor")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_PATH)
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

# 2. Define schema
schema = StructType([
    StructField("timestamp", LongType()), 
    StructField("status", StringType()),
    StructField("severity", StringType()),
    StructField("source_ip", StringType()),
    StructField("user_id", StringType()),
    StructField("content", StringType())
])

# 3. Read Stream
raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "logs")
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load()
)

# 4. Processing, Filtering & Aggregation
# We filter first to keep the state store small, then group and count.

parsed_df = (
    raw_df
    .select(from_json(col("value").cast("string"), schema).alias("data"))
    .select("data.*")
)

events_df = (
    parsed_df
    .withColumn(
        "event_time",
        to_timestamp((col("timestamp") / 1000).cast("double"))
    )
)

filtered_df = (
    events_df
    .filter((lower(col("content")).contains("crash")) & 
            (col("severity").isin("High", "Critical")))
)

aggregated_df = (
    filtered_df
    .withWatermark("event_time", "30 seconds")
    .groupBy(
        window(col("event_time"), "10 seconds"),
        col("user_id")
    )
    .agg(count("*").alias("crash_count"))
    .filter(col("crash_count") > 2)
)

# 5. Writing
query = (
    aggregated_df.writeStream
    .outputMode("append") 
    .format("console")
    .option("truncate", "false")
    .start()
)

query.awaitTermination()