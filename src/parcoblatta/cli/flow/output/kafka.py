from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, Field

from parcoblatta.scanner.validators import ensure_list

from confluent_kafka import Producer


class KafkaConfig(BaseModel):
    bootstrap_servers: Annotated[list[str], BeforeValidator(ensure_list)] = Field(
        default_factory=lambda: ["localhost:9092"],
    )
    client_id: str = "parcoblatta"

    @property
    def producer(config: KafkaConfig) -> Producer:
        return Producer(
            {
                "bootstrap.servers": ",".join(config.bootstrap_servers),
                "client.id": config.client_id,
            },
        )


def publish_kafka_event(producer: Producer | None, topic: str, event: BaseModel) -> None:
    """Publish one event to a Kafka topic.

    :param producer: Kafka producer.
    :param topic: Kafka topic to publish to.
    :param event: Event to publish.
    :return: None.
    """
    if producer is None:
        raise ValueError("producer is required when topics are configured")

    producer.produce(
        topic,
        value=event.model_dump_json().encode("utf-8"),
    )
    producer.poll(0)


def flush_kafka(producer: Producer | None) -> None:
    if producer is not None:
        producer.flush()
