package xz;

import java.nio.ByteBuffer;

import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.Consumer;
import org.apache.pulsar.client.api.Message;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class Activate 
{
    private static final Logger logger = LoggerFactory.getLogger(Activate.class);

    public static void main( String[] args )
    {
        logger.info( "Activating throughput Pulsar function." );

        try{
            PulsarClient client = PulsarClient.builder()
                .serviceUrl("pulsar://localhost:6650")
                .build();
            Producer producer = client.newProducer()
                .topic("throughput-activate")
                .create();
            logger.info("Sending activation signal.");
            String command = "activate!";
            producer.send(command.getBytes());
            producer.close();
            logger.info("Collecting result.");
            Consumer consumer = client.newConsumer()
                .topic("throughput")
                .subscriptionName("my-subscription")
                .subscribe();
            Message msg = consumer.receive();
            logger.info(new String(msg.getData()));
            consumer.acknowledge(msg);
            client.close();
        }catch(Exception ex){
            logger.warn("Failed to send message");
        }        
    }
}